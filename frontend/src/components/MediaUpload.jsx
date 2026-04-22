/**
 * Module: frontend/src/components/MediaUpload.jsx
 * Purpose: File picker with preview, upload progress, and encrypted file sending.
 *          Renders a paperclip/attach button next to the message input.
 * Created by: TASK-19
 *
 * Supports: images (jpeg, png, gif, webp), video (mp4, webm), audio (mp3, ogg, wav)
 * Max file size: 50MB
 */

import { useState, useRef } from 'react';
import { formatBytes } from '../utils/cryptoUtils';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const ACCEPTED_TYPES = 'image/jpeg,image/png,image/gif,image/webp,video/mp4,video/webm,video/quicktime,video/x-msvideo,video/x-matroska,video/3gpp,audio/mpeg,audio/ogg,audio/wav,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/zip,application/x-zip-compressed,text/plain,text/csv';
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

// Map file extensions to display icons
const DOC_ICONS = {
  pdf: '📄', doc: '📝', docx: '📝',
  xls: '📊', xlsx: '📊', csv: '📊',
  ppt: '📽️', pptx: '📽️',
  zip: '🗜️', txt: '📃',
};

export function MediaUpload({ currentUser, selectedUser, disabled, onMediaSent }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError('');

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large (${formatBytes(file.size)}). Maximum is 50MB.`);
      return;
    }

    setSelectedFile(file);

    // Generate preview
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (ev) => setPreview({ type: 'image', url: ev.target.result });
      reader.readAsDataURL(file);
    } else if (file.type.startsWith('video/')) {
      const url = URL.createObjectURL(file);
      setPreview({ type: 'video', url });
    } else if (file.type.startsWith('audio/')) {
      const url = URL.createObjectURL(file);
      setPreview({ type: 'audio', url });
    } else {
      // Document — use icon-based preview
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      setPreview({ type: 'document', icon: DOC_ICONS[ext] || '📎', ext });
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setPreview(null);
    setError('');
    setProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
    // Revoke object URLs to free memory
    if (preview?.url && (preview.type === 'video' || preview.type === 'audio')) {
      URL.revokeObjectURL(preview.url);
    }
  };

  const handleUpload = () => {
    if (!selectedFile || !selectedUser || disabled) return;

    setUploading(true);
    setProgress(0);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('sender', currentUser);
    formData.append('receiver', selectedUser);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        setProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const result = JSON.parse(xhr.responseText);
        // Notify parent that a media message was sent
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
        handleCancel();
      } else {
        try {
          const errData = JSON.parse(xhr.responseText);
          setError(errData.detail || 'Upload failed.');
        } catch {
          setError(`Upload failed (HTTP ${xhr.status}).`);
        }
      }
      setUploading(false);
    });

    xhr.addEventListener('error', () => {
      setError('Upload failed. Check your connection.');
      setUploading(false);
    });

    xhr.open('POST', `${API_BASE}/upload`);
    xhr.send(formData);
  };

  return (
    <>
      {/* Attach button */}
      <button
        className="media-attach-btn"
        onClick={() => fileInputRef.current?.click()}
        disabled={!selectedUser || disabled}
        title="Attach file (image, video, audio, document)"
        id="media-attach-btn"
      >
        📎
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        id="media-file-input"
      />

      {/* Preview overlay */}
      {selectedFile && (
        <div className="media-preview-overlay" id="media-preview-overlay">
          <div className="media-preview-card">
            <div className="media-preview-header">
              <h4>📎 Send File</h4>
              <button className="media-preview-close" onClick={handleCancel}>✕</button>
            </div>

            {/* Preview content */}
            <div className="media-preview-content">
              {preview?.type === 'image' && (
                <img src={preview.url} alt="Preview" className="media-preview-image" />
              )}
              {preview?.type === 'video' && (
                <video src={preview.url} className="media-preview-video" controls muted />
              )}
              {preview?.type === 'audio' && (
                <audio src={preview.url} className="media-preview-audio" controls />
              )}
              {preview?.type === 'document' && (
                <div className="media-preview-document">
                  <span className="media-preview-doc-icon">{preview.icon}</span>
                  <span className="media-preview-doc-ext">.{preview.ext}</span>
                </div>
              )}
            </div>

            {/* File info */}
            <div className="media-preview-info">
              <span className="media-filename">{selectedFile.name}</span>
              <span className="media-filesize">{formatBytes(selectedFile.size)}</span>
            </div>

            {/* Progress bar */}
            {uploading && (
              <div className="media-progress-container">
                <div className="media-progress-bar" style={{ width: `${progress}%` }} />
                <span className="media-progress-text">{progress}%</span>
              </div>
            )}

            {/* Error */}
            {error && <div className="media-upload-error">{error}</div>}

            {/* Actions */}
            <div className="media-preview-actions">
              <button
                className="media-cancel-btn"
                onClick={handleCancel}
                disabled={uploading}
              >
                Cancel
              </button>
              <button
                className="media-send-btn"
                onClick={handleUpload}
                disabled={uploading || !selectedUser}
              >
                {uploading ? '🔐 Encrypting & Uploading...' : '🔐 Encrypt & Send'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
