/**
 * Module: frontend/src/components/ChatWindow.jsx
 * Purpose: Main chat area displaying message history between two users.
 * Created by: TASK-10
 */

import { useEffect, useRef } from 'react';
import { formatTimestamp } from '../utils/cryptoUtils';

export function ChatWindow({ messages, currentUser, selectedUser }) {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Filter messages for the current conversation — only show messages
  // between currentUser and selectedUser (in both directions)
  const conversationMessages = messages.filter(msg =>
    (msg.sender === currentUser && msg.receiver === selectedUser) ||
    (msg.sender === selectedUser && msg.receiver === currentUser)
  );

  if (!selectedUser) {
    return (
      <div className="messages-container">
        <div className="no-chat-selected">
          <div className="shield-icon">🛡️</div>
          <h3>Post-Quantum Secure</h3>
          <p>
            Select a user from the sidebar to start an end-to-end encrypted conversation
            powered by Kyber512 + ML-DSA-44.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="messages-container" id="messages-container">
      {conversationMessages.length === 0 && (
        <div className="no-chat-selected">
          <div className="shield-icon" style={{ fontSize: '2.5rem' }}>💬</div>
          <h3>Start a conversation</h3>
          <p>
            Send a message to {selectedUser}. Everything is encrypted with
            Kyber512 KEM + AES-256-GCM and signed with ML-DSA-44.
          </p>
        </div>
      )}

      {conversationMessages.map(msg => (
        <div
          key={msg.id}
          className={`message-bubble ${msg.direction}`}
          id={`msg-${msg.id}`}
        >
          <div className="message-text">{msg.plaintext}</div>
          <div className="message-meta">
            <span>{formatTimestamp(msg.timestamp)}</span>
            {msg.direction === 'received' && msg.signatureValid !== undefined && (
              <span className="sig-badge">
                {msg.signatureValid ? '✓ Verified' : '✗ Unverified'}
              </span>
            )}
          </div>
        </div>
      ))}

      <div ref={messagesEndRef} />
    </div>
  );
}
