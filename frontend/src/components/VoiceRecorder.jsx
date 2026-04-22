/**
 * Module: frontend/src/components/VoiceRecorder.jsx
 * Purpose: Record voice messages using the browser's MediaRecorder API.
 *          Shows a live recording timer and animated indicator.
 *          Sends the recorded audio as an encrypted media file.
 * Created by: Enhancement — Voice Messages
 */

import { useState, useRef, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export function VoiceRecorder({ currentUser, selectedUser, disabled, onMediaSent }) {
  const [recording, setRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  const formatDuration = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const startRecording = useCallback(async () => {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      };

      mediaRecorder.start(100); // collect data every 100ms
      setRecording(true);
      setDuration(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);

    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone permissions.');
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone.');
      } else {
        setError(`Recording failed: ${err.message}`);
      }
    }
  }, []);

  const stopAndSend = useCallback(async () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') return;

    // Stop timer
    clearInterval(timerRef.current);
    timerRef.current = null;

    // Stop recording
    const recorder = mediaRecorderRef.current;

    // Wait for the recorder to actually stop and collect all data
    await new Promise((resolve) => {
      recorder.onstop = () => {
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        resolve();
      };
      recorder.stop();
    });

    setRecording(false);

    // Build the audio blob
    const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });

    if (audioBlob.size < 100) {
      setError('Recording too short. Try again.');
      return;
    }

    // Upload
    setUploading(true);
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const filename = `voice_${timestamp}.webm`;

    const formData = new FormData();
    formData.append('file', audioBlob, filename);
    formData.append('sender', currentUser);
    formData.append('receiver', selectedUser);

    try {
      const resp = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed (HTTP ${resp.status})`);
      }

      const result = await resp.json();

      if (onMediaSent) {
        onMediaSent({
          type: 'media_message',
          media_id: result.media_id,
          sender: currentUser,
          receiver: selectedUser,
          file_type: result.file_type,
          original_filename: result.original_filename,
          file_size_bytes: result.file_size_bytes,
          direction: 'sent',
          timestamp: result.timestamp || new Date().toISOString(),
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to send voice message.');
    } finally {
      setUploading(false);
      setDuration(0);
      chunksRef.current = [];
    }
  }, [currentUser, selectedUser, onMediaSent]);

  const cancelRecording = useCallback(() => {
    clearInterval(timerRef.current);
    timerRef.current = null;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    setRecording(false);
    setDuration(0);
    chunksRef.current = [];
  }, []);

  // Recording mode: show timer + stop/cancel buttons
  if (recording) {
    return (
      <div className="voice-recorder-active" id="voice-recorder-active">
        <div className="voice-recording-indicator">
          <span className="voice-recording-dot" />
          <span className="voice-recording-label">Recording</span>
          <span className="voice-recording-timer">{formatDuration(duration)}</span>
        </div>
        <div className="voice-recording-actions">
          <button
            className="voice-cancel-btn"
            onClick={cancelRecording}
            title="Cancel recording"
          >
            ✕
          </button>
          <button
            className="voice-send-btn"
            onClick={stopAndSend}
            title="Stop & send"
          >
            ⬆
          </button>
        </div>
      </div>
    );
  }

  // Uploading state
  if (uploading) {
    return (
      <div className="voice-recorder-uploading">
        <span className="voice-uploading-text">🔐 Encrypting voice...</span>
      </div>
    );
  }

  // Default: mic button
  return (
    <>
      <button
        className="voice-record-btn"
        onClick={startRecording}
        disabled={!selectedUser || disabled}
        title="Record voice message"
        id="voice-record-btn"
      >
        🎤
      </button>
      {error && (
        <div className="voice-error" onClick={() => setError('')}>
          ⚠️ {error}
        </div>
      )}
    </>
  );
}
