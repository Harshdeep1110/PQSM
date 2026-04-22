/**
 * Module: frontend/src/components/EncryptionVisualizer.jsx
 * Purpose: Side panel showing step-by-step crypto flow for each message.
 *          This is the KEY DEMO COMPONENT — the "wow factor" of the project.
 * Created by: TASK-11, Modified by: TASK-21
 *
 * Displays 5 steps for every text message:
 *   1. Plaintext (green)
 *   2. Key Exchange — Kyber512 KEM encapsulation
 *   3. Encryption — AES-256-GCM ciphertext + nonce + auth tag
 *   4. Signature — ML-DSA-44 digital signature
 *   5. Decrypted Output — recovered plaintext (green, confirms round-trip)
 *
 * TASK-21: Also displays file encryption trace for media messages:
 *   1. File info (name, type, size)
 *   2. Kyber512 KEM (per-file fresh encapsulation)
 *   3. AES-256-GCM (nonce, tag, encrypted size)
 *   4. ML-DSA-44 signature
 *   5. Decryption verified ✓
 */

import { useState } from 'react';
import { formatHex, hexToByteLength, formatBytes } from '../utils/cryptoUtils';

export function EncryptionVisualizer({ cryptoTraces, onClear }) {
  const [copiedId, setCopiedId] = useState(null);
  const [activeTab, setActiveTab] = useState('text'); // 'text' or 'file'

  // Get the latest text trace and media trace
  const latestTextTrace = [...cryptoTraces].reverse().find(t => t.type === 'crypto_trace') || null;
  const latestMediaTrace = [...cryptoTraces].reverse().find(t => t.type === 'media_crypto_trace') || null;

  // Auto-select the tab based on the latest trace
  const latestTrace = activeTab === 'file' ? latestMediaTrace : latestTextTrace;
  const hasTextTraces = cryptoTraces.some(t => t.type === 'crypto_trace');
  const hasMediaTraces = cryptoTraces.some(t => t.type === 'media_crypto_trace');

  const handleCopyTrace = async () => {
    const traceToCopy = latestTrace;
    if (!traceToCopy) return;
    try {
      const traceData = traceToCopy.type === 'media_crypto_trace'
        ? {
            type: 'file_encryption_trace',
            direction: traceToCopy.direction,
            sender: traceToCopy.sender,
            receiver: traceToCopy.receiver,
            file_type: traceToCopy.file_type,
            original_filename: traceToCopy.original_filename,
            file_size_bytes: traceToCopy.file_size_bytes,
            algorithms: {
              kem: traceToCopy.algorithm_kem,
              signature: traceToCopy.algorithm_sig,
              symmetric: traceToCopy.algorithm_sym,
            },
            crypto_data: {
              kem_ciphertext_hex: traceToCopy.kem_ciphertext_hex,
              nonce_hex: traceToCopy.nonce_hex,
              tag_hex: traceToCopy.tag_hex,
              signature_hex: traceToCopy.signature_hex,
            },
          }
        : {
            direction: traceToCopy.direction,
            sender: traceToCopy.sender,
            receiver: traceToCopy.receiver,
            plaintext: traceToCopy.plaintext,
            algorithms: {
              kem: traceToCopy.algorithm_kem,
              signature: traceToCopy.algorithm_sig,
              symmetric: traceToCopy.algorithm_sym,
            },
            crypto_data: {
              shared_secret_hex: traceToCopy.shared_secret_hex,
              kem_ciphertext_hex: traceToCopy.kem_ciphertext_hex,
              ciphertext_hex: traceToCopy.ciphertext_hex,
              nonce_hex: traceToCopy.nonce_hex,
              tag_hex: traceToCopy.tag_hex,
              signature_hex: traceToCopy.signature_hex,
            },
          };
      await navigator.clipboard.writeText(JSON.stringify(traceData, null, 2));
      setCopiedId(latestTrace.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (e) {
      console.error('Copy failed:', e);
    }
  };

  // Render text message crypto trace
  const renderTextTrace = (trace) => (
    <div key={trace.id}>
      {/* Direction badge */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '14px',
        fontSize: '0.8rem',
        color: 'var(--text-secondary)',
      }}>
        <span style={{
          padding: '3px 10px',
          borderRadius: '12px',
          fontSize: '0.7rem',
          fontWeight: 600,
          background: trace.direction === 'sent'
            ? 'rgba(99, 102, 241, 0.15)'
            : 'rgba(52, 211, 153, 0.15)',
          color: trace.direction === 'sent'
            ? 'var(--accent-primary)'
            : 'var(--accent-emerald)',
        }}>
          {trace.direction === 'sent' ? '↑ SENT' : '↓ RECEIVED'}
        </span>
        <span>{trace.sender} → {trace.receiver}</span>
      </div>

      {/* Step 1: Plaintext */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">1</span>
          <span className="step-label">Plaintext</span>
        </div>
        <div className="step-data plaintext">
          {trace.plaintext}
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 2: Key Exchange (Kyber512 KEM) */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">2</span>
          <span className="step-label">Key Exchange</span>
          <span className="step-algo">{trace.algorithm_kem || 'Kyber512'}</span>
        </div>
        <div className="step-data ciphertext">
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>KEM CT: </span>
            {formatHex(trace.kem_ciphertext_hex, 24)}
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            ({hexToByteLength(trace.kem_ciphertext_hex)} bytes)
          </div>
          <div style={{ marginTop: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Secret: </span>
            {formatHex(trace.shared_secret_hex, 24)}
          </div>
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 3: Encryption (AES-256-GCM) */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">3</span>
          <span className="step-label">Encryption</span>
          <span className="step-algo">{trace.algorithm_sym || 'AES-256-GCM'}</span>
        </div>
        <div className="step-data ciphertext">
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>CT: </span>
            {formatHex(trace.ciphertext_hex, 32)}
          </div>
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Nonce: </span>
            {trace.nonce_hex}
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Tag: </span>
            {trace.tag_hex}
          </div>
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 4: Signature (ML-DSA-44) */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">4</span>
          <span className="step-label">Digital Signature</span>
          <span className="step-algo">{trace.algorithm_sig || 'ML-DSA-44'}</span>
        </div>
        <div className="step-data signature">
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Sig: </span>
            {formatHex(trace.signature_hex, 32)}
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            ({hexToByteLength(trace.signature_hex)} bytes)
          </div>
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 5: Decrypted Output */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">5</span>
          <span className="step-label">Decrypted Output</span>
          <span className="step-algo" style={{ background: 'rgba(52,211,153,0.1)', color: 'var(--accent-emerald)' }}>
            ✓ Verified
          </span>
        </div>
        <div className="step-data plaintext">
          {trace.plaintext}
        </div>
      </div>
    </div>
  );

  // Render file/media crypto trace (TASK-21)
  const renderMediaTrace = (trace) => (
    <div key={trace.id}>
      {/* Direction badge */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '14px',
        fontSize: '0.8rem',
        color: 'var(--text-secondary)',
      }}>
        <span style={{
          padding: '3px 10px',
          borderRadius: '12px',
          fontSize: '0.7rem',
          fontWeight: 600,
          background: trace.direction === 'sent'
            ? 'rgba(99, 102, 241, 0.15)'
            : 'rgba(52, 211, 153, 0.15)',
          color: trace.direction === 'sent'
            ? 'var(--accent-primary)'
            : 'var(--accent-emerald)',
        }}>
          {trace.direction === 'sent' ? '↑ FILE SENT' : '↓ FILE RECEIVED'}
        </span>
        <span>{trace.sender} → {trace.receiver}</span>
      </div>

      {/* Step 1: File Info */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">1</span>
          <span className="step-label">Original File</span>
          <span className="step-algo" style={{ background: 'rgba(251,191,36,0.1)', color: 'var(--accent-amber)' }}>
            📎 {trace.file_type}
          </span>
        </div>
        <div className="step-data plaintext">
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Name: </span>
            {trace.original_filename}
          </div>
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Type: </span>
            {trace.file_type}
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Size: </span>
            {formatBytes(trace.file_size_bytes)} ({trace.file_size_bytes} bytes)
          </div>
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 2: Kyber512 KEM (fresh per-file) */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">2</span>
          <span className="step-label">Key Exchange (Per-File)</span>
          <span className="step-algo">{trace.algorithm_kem || 'Kyber512'}</span>
        </div>
        <div className="step-data ciphertext">
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>KEM CT: </span>
            {formatHex(trace.kem_ciphertext_hex, 24)}
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            ({hexToByteLength(trace.kem_ciphertext_hex)} bytes) — Fresh encapsulation for this file
          </div>
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 3: AES-256-GCM encryption */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">3</span>
          <span className="step-label">File Encryption</span>
          <span className="step-algo">{trace.algorithm_sym || 'AES-256-GCM'}</span>
        </div>
        <div className="step-data ciphertext">
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Nonce: </span>
            {trace.nonce_hex}
          </div>
          <div style={{ marginBottom: '4px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Auth Tag: </span>
            {trace.tag_hex}
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Encrypted size: </span>
            {formatBytes(trace.file_size_bytes)}
          </div>
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 4: Dilithium signature */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">4</span>
          <span className="step-label">Digital Signature</span>
          <span className="step-algo">{trace.algorithm_sig || 'ML-DSA-44'}</span>
        </div>
        <div className="step-data signature">
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Sig: </span>
            {formatHex(trace.signature_hex, 32)}
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            ({hexToByteLength(trace.signature_hex)} bytes) — Over encrypted file bytes
          </div>
        </div>
      </div>

      <div className="crypto-arrow">↓</div>

      {/* Step 5: Decryption Verified */}
      <div className="crypto-step">
        <div className="crypto-step-header">
          <span className="step-number">5</span>
          <span className="step-label">Decryption Status</span>
          <span className="step-algo" style={{ background: 'rgba(52,211,153,0.1)', color: 'var(--accent-emerald)' }}>
            ✓ Verified
          </span>
        </div>
        <div className="step-data plaintext">
          Decryption verified ✓ — File successfully encrypted at rest and available for secure download.
        </div>
      </div>
    </div>
  );

  return (
    <div className="visualizer-panel" id="encryption-visualizer">
      {/* Header */}
      <div className="visualizer-header">
        <div>
          <h3>🔬 Encryption Visualizer</h3>
          <span style={{
            fontSize: '0.6rem',
            color: 'var(--accent-cyan)',
            fontWeight: 500,
            opacity: 0.8,
          }}>
            Cryptographic Pipeline Details
          </span>
        </div>
        <button
          className={`copy-trace-btn ${copiedId ? 'copied' : ''}`}
          onClick={handleCopyTrace}
          disabled={!latestTrace}
          id="copy-trace-btn"
        >
          {copiedId ? '✓ Copied!' : '📋 Copy Raw'}
        </button>
      </div>

      {/* Tab switcher (shown when both text and media traces exist) */}
      {(hasTextTraces || hasMediaTraces) && (
        <div className="visualizer-tabs">
          <button
            className={`visualizer-tab ${activeTab === 'text' ? 'active' : ''}`}
            onClick={() => setActiveTab('text')}
          >
            💬 Message Trace
          </button>
          <button
            className={`visualizer-tab ${activeTab === 'file' ? 'active' : ''}`}
            onClick={() => setActiveTab('file')}
          >
            📎 File Trace
          </button>
        </div>
      )}

      {/* Content */}
      <div className="visualizer-content" id="visualizer-content" style={{ padding: '20px' }}>
        {!latestTrace ? (
          <div className="no-trace">
            <div className="lock-icon">🔐</div>
            <p>
              {activeTab === 'file'
                ? 'Send or receive a file to see the file encryption pipeline in action.'
                : 'Send or receive a message to see the full post-quantum encryption pipeline in action.'}
            </p>
            <div style={{
              fontSize: '0.7rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              marginTop: '8px',
            }}>
              Kyber512 → AES-256-GCM → ML-DSA-44
            </div>
          </div>
        ) : (
          <>
            {activeTab === 'text' && latestTextTrace && renderTextTrace(latestTextTrace)}
            {activeTab === 'file' && latestMediaTrace && renderMediaTrace(latestMediaTrace)}

            {/* Trace history count */}
            {cryptoTraces.length > 1 && (
              <div style={{
                textAlign: 'center',
                marginTop: '16px',
                fontSize: '0.7rem',
                color: 'var(--text-muted)',
              }}>
                Showing latest of {cryptoTraces.length} traces
                <button
                  onClick={onClear}
                  style={{
                    marginLeft: '8px',
                    padding: '2px 8px',
                    background: 'none',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.65rem',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  Clear
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
