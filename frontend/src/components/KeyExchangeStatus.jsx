/**
 * Module: frontend/src/components/KeyExchangeStatus.jsx
 * Purpose: Status badge showing the current PQC session security state.
 *          Displays algorithm names and truncated public key fingerprint.
 * Created by: TASK-12
 */

import { formatHex } from '../utils/cryptoUtils';

export function KeyExchangeStatus({ selectedUser, users, connected }) {
  // Find the selected user's public key info
  const userInfo = users.find(u => u.username === selectedUser);

  if (!selectedUser) return null;

  const isReady = connected && userInfo;

  return (
    <div
      className={`key-exchange-status ${isReady ? '' : 'pending'}`}
      id="key-exchange-status"
      title={
        userInfo
          ? `Kyber Public Key: ${userInfo.public_key_kyber_hex?.substring(0, 32)}...`
          : 'Waiting for key exchange...'
      }
    >
      <span className="key-icon">{isReady ? '🔐' : '⏳'}</span>
      {isReady ? (
        <>
          <span>Kyber512 + ML-DSA-44</span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6rem',
            opacity: 0.7,
            marginLeft: '4px',
          }}>
            [{formatHex(userInfo?.public_key_kyber_hex, 8)}]
          </span>
        </>
      ) : (
        <span>Key exchange pending...</span>
      )}
    </div>
  );
}
