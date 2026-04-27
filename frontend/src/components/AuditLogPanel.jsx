/**
 * Module: frontend/src/components/AuditLogPanel.jsx
 * Purpose: Displays cryptographic audit log entries from Cloud Logging.
 *          Shows a timeline of all crypto operations with event type,
 *          algorithm, timestamp, and success/failure status.
 * Created by: TASK-30 (Phase 7 — Google Cloud Integration)
 */

import { useState, useEffect, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Event type display config
const EVENT_CONFIG = {
  key_generation:     { icon: '🔑', label: 'Key Generation',    color: '#fbbf24' },
  kem_encapsulation:  { icon: '📦', label: 'KEM Encapsulate',   color: '#6366f1' },
  kem_decapsulation:  { icon: '📭', label: 'KEM Decapsulate',   color: '#8b5cf6' },
  aes_encrypt:        { icon: '🔒', label: 'AES Encrypt',       color: '#22d3ee' },
  aes_decrypt:        { icon: '🔓', label: 'AES Decrypt',       color: '#34d399' },
  signature_sign:     { icon: '✍️', label: 'Sign',              color: '#a78bfa' },
  signature_verify:   { icon: '✅', label: 'Verify Signature',  color: '#34d399' },
  kms_wrap:           { icon: '🛡️', label: 'KMS Wrap',          color: '#f472b6' },
  kms_unwrap:         { icon: '🔓', label: 'KMS Unwrap',        color: '#fb923c' },
};

export function AuditLogPanel() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await fetch(`${API_BASE}/audit/logs?limit=50`);
      if (resp.ok) {
        const data = await resp.json();
        setLogs(data.logs || []);
      }
    } catch (e) {
      console.error('Failed to fetch audit logs:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchLogs();
    if (!autoRefresh) return;
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, [fetchLogs, autoRefresh]);

  const formatTime = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false,
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="audit-log-panel" id="audit-log-panel">
      {/* Header */}
      <div className="audit-log-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Cryptographic Audit Trail
          </span>
          <span style={{
            fontSize: '0.6rem',
            padding: '2px 6px',
            borderRadius: '8px',
            background: 'rgba(52,211,153,0.1)',
            color: 'var(--accent-emerald)',
            fontFamily: 'var(--font-mono)',
          }}>
            Cloud Logging
          </span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{
              padding: '3px 8px',
              background: autoRefresh ? 'rgba(52,211,153,0.1)' : 'rgba(100,116,139,0.1)',
              border: `1px solid ${autoRefresh ? 'rgba(52,211,153,0.2)' : 'rgba(100,116,139,0.2)'}`,
              borderRadius: '6px',
              color: autoRefresh ? 'var(--accent-emerald)' : 'var(--text-muted)',
              fontSize: '0.6rem',
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
            }}
          >
            {autoRefresh ? '⏸ Live' : '▶ Paused'}
          </button>
          <button
            onClick={fetchLogs}
            disabled={loading}
            style={{
              padding: '3px 8px',
              background: 'rgba(99,102,241,0.1)',
              border: '1px solid rgba(99,102,241,0.2)',
              borderRadius: '6px',
              color: 'var(--accent-primary)',
              fontSize: '0.6rem',
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
            }}
          >
            🔄
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div className="audit-log-entries">
        {logs.length === 0 ? (
          <div className="no-trace">
            <div className="lock-icon">📋</div>
            <p>No audit logs yet. Send a message to see crypto operations logged here.</p>
            <div style={{
              fontSize: '0.65rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              marginTop: '4px',
            }}>
              Google Cloud Logging Integration
            </div>
          </div>
        ) : (
          logs.map((log, idx) => {
            const config = EVENT_CONFIG[log.event_type] || {
              icon: '⚡', label: log.event_type, color: '#94a3b8',
            };
            return (
              <div
                key={idx}
                className="audit-log-entry"
                style={{ animationDelay: `${idx * 30}ms` }}
              >
                <div className="audit-log-icon" style={{ color: config.color }}>
                  {config.icon}
                </div>
                <div className="audit-log-details">
                  <div className="audit-log-event">
                    <span style={{ color: config.color, fontWeight: 600 }}>
                      {config.label}
                    </span>
                    <span className="audit-log-algo">{log.algorithm}</span>
                  </div>
                  <div className="audit-log-meta">
                    <span>🕐 {formatTime(log.timestamp)}</span>
                    <span>👤 {log.user_id_hash}</span>
                    <span>{log.duration_ms.toFixed(1)}ms</span>
                  </div>
                </div>
                <div className={`audit-log-status ${log.success ? 'success' : 'failure'}`}>
                  {log.success ? '✓' : '✗'}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      {logs.length > 0 && (
        <div style={{
          padding: '8px 16px',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '0.6rem',
          color: 'var(--text-muted)',
          textAlign: 'center',
        }}>
          {logs.length} entries • {autoRefresh ? 'Auto-refreshing every 10s' : 'Paused'}
        </div>
      )}
    </div>
  );
}
