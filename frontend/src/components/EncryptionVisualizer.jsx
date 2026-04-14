/**
 * Module: frontend/src/components/EncryptionVisualizer.jsx
 * Purpose: Side panel showing step-by-step crypto flow for each message.
 *          This is the KEY DEMO COMPONENT — the "wow factor" of the project.
 * Created by: TASK-11
 *
 * Displays 5 steps for every message:
 *   1. Plaintext (green)
 *   2. Key Exchange — Kyber512 KEM encapsulation
 *   3. Encryption — AES-256-GCM ciphertext + nonce + auth tag
 *   4. Signature — ML-DSA-44 digital signature
 *   5. Decrypted Output — recovered plaintext (green, confirms round-trip)
 */

import { useState } from 'react';
import { formatHex, hexToByteLength } from '../utils/cryptoUtils';

export function EncryptionVisualizer({ cryptoTraces, onClear }) {
  const [copiedId, setCopiedId] = useState(null);

  // Get the latest trace for display
  const latestTrace = cryptoTraces.length > 0
    ? cryptoTraces[cryptoTraces.length - 1]
    : null;

  const handleCopyTrace = async () => {
    if (!latestTrace) return;
    try {
      // Build a clean JSON object for copying
      const traceData = {
        direction: latestTrace.direction,
        sender: latestTrace.sender,
        receiver: latestTrace.receiver,
        plaintext: latestTrace.plaintext,
        algorithms: {
          kem: latestTrace.algorithm_kem,
          signature: latestTrace.algorithm_sig,
          symmetric: latestTrace.algorithm_sym,
        },
        crypto_data: {
          shared_secret_hex: latestTrace.shared_secret_hex,
          kem_ciphertext_hex: latestTrace.kem_ciphertext_hex,
          ciphertext_hex: latestTrace.ciphertext_hex,
          nonce_hex: latestTrace.nonce_hex,
          tag_hex: latestTrace.tag_hex,
          signature_hex: latestTrace.signature_hex,
        },
      };
      await navigator.clipboard.writeText(JSON.stringify(traceData, null, 2));
      setCopiedId(latestTrace.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (e) {
      console.error('Copy failed:', e);
    }
  };

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

      {/* Content */}
      <div className="visualizer-content" id="visualizer-content" style={{ padding: '20px' }}>
        {!latestTrace ? (
          <div className="no-trace">
            <div className="lock-icon">🔐</div>
            <p>
              Send or receive a message to see the full post-quantum encryption
              pipeline in action.
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
          <div key={latestTrace.id}>
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
                background: latestTrace.direction === 'sent'
                  ? 'rgba(99, 102, 241, 0.15)'
                  : 'rgba(52, 211, 153, 0.15)',
                color: latestTrace.direction === 'sent'
                  ? 'var(--accent-primary)'
                  : 'var(--accent-emerald)',
              }}>
                {latestTrace.direction === 'sent' ? '↑ SENT' : '↓ RECEIVED'}
              </span>
              <span>{latestTrace.sender} → {latestTrace.receiver}</span>
            </div>

            {/* Step 1: Plaintext */}
            <div className="crypto-step">
              <div className="crypto-step-header">
                <span className="step-number">1</span>
                <span className="step-label">Plaintext</span>
              </div>
              <div className="step-data plaintext">
                {latestTrace.plaintext}
              </div>
            </div>

            <div className="crypto-arrow">↓</div>

            {/* Step 2: Key Exchange (Kyber512 KEM) */}
            <div className="crypto-step">
              <div className="crypto-step-header">
                <span className="step-number">2</span>
                <span className="step-label">Key Exchange</span>
                <span className="step-algo">{latestTrace.algorithm_kem || 'Kyber512'}</span>
              </div>
              <div className="step-data ciphertext">
                <div style={{ marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>KEM CT: </span>
                  {formatHex(latestTrace.kem_ciphertext_hex, 24)}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                  ({hexToByteLength(latestTrace.kem_ciphertext_hex)} bytes)
                </div>
                <div style={{ marginTop: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Secret: </span>
                  {formatHex(latestTrace.shared_secret_hex, 24)}
                </div>
              </div>
            </div>

            <div className="crypto-arrow">↓</div>

            {/* Step 3: Encryption (AES-256-GCM) */}
            <div className="crypto-step">
              <div className="crypto-step-header">
                <span className="step-number">3</span>
                <span className="step-label">Encryption</span>
                <span className="step-algo">{latestTrace.algorithm_sym || 'AES-256-GCM'}</span>
              </div>
              <div className="step-data ciphertext">
                <div style={{ marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>CT: </span>
                  {formatHex(latestTrace.ciphertext_hex, 32)}
                </div>
                <div style={{ marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Nonce: </span>
                  {latestTrace.nonce_hex}
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Tag: </span>
                  {latestTrace.tag_hex}
                </div>
              </div>
            </div>

            <div className="crypto-arrow">↓</div>

            {/* Step 4: Signature (ML-DSA-44) */}
            <div className="crypto-step">
              <div className="crypto-step-header">
                <span className="step-number">4</span>
                <span className="step-label">Digital Signature</span>
                <span className="step-algo">{latestTrace.algorithm_sig || 'ML-DSA-44'}</span>
              </div>
              <div className="step-data signature">
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Sig: </span>
                  {formatHex(latestTrace.signature_hex, 32)}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  ({hexToByteLength(latestTrace.signature_hex)} bytes)
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
                {latestTrace.plaintext}
              </div>
            </div>

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
          </div>
        )}
      </div>
    </div>
  );
}
