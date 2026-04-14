/**
 * Module: frontend/src/components/UserList.jsx
 * Purpose: Sidebar showing online users. Click to open a chat.
 * Created by: TASK-10
 */

import { formatHex } from '../utils/cryptoUtils';

export function UserList({ users, usersOnline, currentUser, selectedUser, onSelectUser, onLogout }) {
  // Filter out the current user from the list
  const otherUsers = users.filter(u => u.username !== currentUser);

  return (
    <aside className="sidebar" id="sidebar-user-list">
      {/* Header */}
      <div className="sidebar-header">
        <h2>PQC Messenger</h2>
        <div className="connection-status">
          <span className={`status-dot ${usersOnline.includes(currentUser) ? '' : 'offline'}`}></span>
          <span>{usersOnline.length} user{usersOnline.length !== 1 ? 's' : ''} online</span>
        </div>
      </div>

      {/* User List */}
      <div className="user-list" id="user-list">
        {otherUsers.length === 0 && (
          <div style={{
            padding: '24px 16px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
          }}>
            No other users registered yet.
            <br />
            <span style={{ fontSize: '0.75rem', marginTop: '8px', display: 'block' }}>
              Open another tab and register a new user to start chatting.
            </span>
          </div>
        )}

        {otherUsers.map(user => {
          const isOnline = usersOnline.includes(user.username);
          const isActive = selectedUser === user.username;

          return (
            <div
              key={user.username}
              className={`user-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectUser(user.username)}
              id={`user-item-${user.username}`}
            >
              <div className="user-avatar">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="user-info">
                <div className="user-name">{user.username}</div>
                <div className="user-key-fingerprint">
                  {formatHex(user.public_key_kyber_hex, 12)}
                </div>
              </div>
              {isOnline && <div className="user-online-dot" title="Online"></div>}
            </div>
          );
        })}
      </div>

      {/* Footer — Current User */}
      <div className="sidebar-footer">
        <div className="user-avatar" style={{ width: 32, height: 32, fontSize: '0.75rem' }}>
          {currentUser.charAt(0).toUpperCase()}
        </div>
        <div className="current-user-tag">
          Logged in as <span className="current-user-name">{currentUser}</span>
        </div>
        <button className="logout-btn" onClick={onLogout} id="logout-btn">
          Logout
        </button>
      </div>
    </aside>
  );
}
