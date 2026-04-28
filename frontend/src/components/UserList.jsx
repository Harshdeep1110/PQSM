/**
 * Module: frontend/src/components/UserList.jsx
 * Purpose: Sidebar showing online users. Click to open a chat.
 * Created by: TASK-10
 */

import { formatHex } from '../utils/cryptoUtils';
import { useTheme } from '../hooks/useTheme';

/* ── Inline SVG icons (no extra dependency) ── */
const SunIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </svg>
);

const MoonIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

export function UserList({ users, usersOnline, currentUser, selectedUser, onSelectUser, onLogout }) {
  const { theme, toggleTheme } = useTheme();

  // Filter out the current user from the list
  const otherUsers = users.filter(u => u.username !== currentUser);

  return (
    <aside className="sidebar" id="sidebar-user-list">
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-title-row">
          <h2>PQC Messenger</h2>
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            id="theme-toggle"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
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

