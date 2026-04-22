/**
 * Module: frontend/src/components/MediaMessage.jsx
 * Purpose: Renders media messages (image, video, audio) in the chat window.
 *          Fetches decrypted content from GET /media/{id} on mount.
 * Created by: TASK-20
 *
 * Shows:
 *   - Images with lightbox expand on click
 *   - Videos with playback controls
 *   - Audio with custom styled player
 *   - "🔐 Encrypted at rest" badge + file name/size caption
 */

import { useState, useEffect } from 'react';
import { formatBytes } from '../utils/cryptoUtils';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Map file extensions to display icons
const DOC_ICONS = {
  pdf: '📄', doc: '📝', docx: '📝',
  xls: '📊', xlsx: '📊', csv: '📊',
  ppt: '📽️', pptx: '📽️',
  zip: '🗜️', txt: '📃',
};

function getDocIcon(filename) {
  const ext = filename?.split('.').pop()?.toLowerCase() || '';
  return DOC_ICONS[ext] || '📎';
}

function isVoiceMessage(filename) {
  return filename?.startsWith('voice_');
}

export function MediaMessage({ mediaId, fileType, originalFilename, fileSizeBytes, sender, currentUser }) {
  const [mediaUrl, setMediaUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  useEffect(() => {
    if (!mediaId) return;

    let objectUrl = null;

    const fetchMedia = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await fetch(
          `${API_BASE}/media/${mediaId}?receiver_username=${currentUser}`
        );
        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          throw new Error(errData.detail || `HTTP ${resp.status}`);
        }
        const blob = await resp.blob();
        objectUrl = URL.createObjectURL(blob);
        setMediaUrl(objectUrl);
      } catch (e) {
        setError(e.message || 'Failed to load media');
      } finally {
        setLoading(false);
      }
    };

    fetchMedia();

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [mediaId, currentUser]);

  return (
    <div className="media-message" id={`media-${mediaId}`}>
      {/* Loading state */}
      {loading && (
        <div className="media-loading">
          <div className="media-loading-spinner" />
          <span>Decrypting file...</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="media-error">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Rendered media */}
      {!loading && !error && mediaUrl && (
        <>
          {fileType === 'image' && (
            <>
              <img
                src={mediaUrl}
                alt={originalFilename}
                className="media-image"
                onClick={() => setLightboxOpen(true)}
              />
              {/* Lightbox */}
              {lightboxOpen && (
                <div
                  className="media-lightbox"
                  onClick={() => setLightboxOpen(false)}
                >
                  <img src={mediaUrl} alt={originalFilename} className="media-lightbox-img" />
                  <button className="media-lightbox-close">✕</button>
                </div>
              )}
            </>
          )}

          {fileType === 'video' && (
            <div className="media-video-container">
              <video
                src={mediaUrl}
                className="media-video"
                controls
                preload="metadata"
              />
              <a
                href={mediaUrl}
                download={originalFilename}
                className="media-download-btn"
                title="Download video"
              >
                ⬇ Download
              </a>
            </div>
          )}

          {fileType === 'audio' && (
            <div className="media-audio-container">
              <span className="media-audio-icon">
                {isVoiceMessage(originalFilename) ? '🎙️' : '🎵'}
              </span>
              <div className="media-audio-inner">
                {isVoiceMessage(originalFilename) && (
                  <span className="media-voice-label">Voice message</span>
                )}
                <audio src={mediaUrl} className="media-audio" controls />
              </div>
            </div>
          )}

          {fileType === 'document' && (
            <div className="media-document-card">
              <span className="media-document-icon">{getDocIcon(originalFilename)}</span>
              <div className="media-document-info">
                <span className="media-document-name">{originalFilename}</span>
                {fileSizeBytes && (
                  <span className="media-document-size">{formatBytes(fileSizeBytes)}</span>
                )}
              </div>
              <a
                href={mediaUrl}
                download={originalFilename}
                className="media-document-download"
                title="Download file"
              >
                ⬇
              </a>
            </div>
          )}
        </>
      )}

      {/* Caption + encrypted badge */}
      <div className="media-caption">
        <div className="media-caption-info">
          <span className="media-caption-name">{originalFilename}</span>
          {fileSizeBytes && (
            <span className="media-caption-size">{formatBytes(fileSizeBytes)}</span>
          )}
        </div>
        <span className="media-encrypted-badge">🔐 Encrypted at rest</span>
      </div>
    </div>
  );
}
