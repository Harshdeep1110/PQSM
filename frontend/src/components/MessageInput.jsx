/**
 * Module: frontend/src/components/MessageInput.jsx
 * Purpose: Text input, send button, media attach button, and voice recorder for composing messages.
 * Created by: TASK-10, Modified by: TASK-19
 */

import { useState } from 'react';

export function MessageInput({ selectedUser, onSendMessage, disabled, currentUser }) {
  const [text, setText] = useState('');

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || !selectedUser || disabled) return;

    onSendMessage(selectedUser, trimmed);
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="message-input-container" id="message-input-container">
      <div className="message-input-wrapper">
        <input
          type="text"
          className="message-input"
          placeholder={
            selectedUser
              ? `Encrypt & send to ${selectedUser}...`
              : 'Select a user to chat'
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!selectedUser || disabled}
          id="message-input"
          autoComplete="off"
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!text.trim() || !selectedUser || disabled}
          id="send-btn"
        >
          <span>🔐</span>
          Send
        </button>
      </div>
    </div>
  );
}
