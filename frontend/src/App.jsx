/**
 * Module: frontend/src/App.jsx
 * Purpose: Top-level application component.
 *          Handles login/signup flow (Firebase or local), layout, and wires all components.
 * Created by: TASK-10, Modified by: TASK-26 (Firebase Auth integration)
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useTheme } from './hooks/useTheme';
import { UserList } from './components/UserList';
import { ChatWindow } from './components/ChatWindow';
import { MessageInput } from './components/MessageInput';
import { EncryptionVisualizer } from './components/EncryptionVisualizer';
import { KeyExchangeStatus } from './components/KeyExchangeStatus';
import { FirebaseAuth } from './components/FirebaseAuth';
import { isFirebaseConfigured } from './services/firebaseConfig';
import './styles/main.css';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/* Small floating theme toggle for the login / pre-auth screens */
function LoginThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      className="theme-toggle-btn login-theme-toggle"
      onClick={toggleTheme}
      id="login-theme-toggle"
      title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      aria-label="Toggle theme"
    >
      {theme === 'dark' ? (
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
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}

function App() {
  // Auth state
  const [currentUser, setCurrentUser] = useState(null);
  const [userKeys, setUserKeys] = useState(null);

  // App state
  const [allUsers, setAllUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showVisualizer, setShowVisualizer] = useState(true);
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [authMode, setAuthMode] = useState('signup'); // 'signup' or 'login'

  // WebSocket hook
  const {
    connected,
    messages,
    setMessages,
    cryptoTraces,
    usersOnline,
    sendMessage,
    clearTraces,
    error: wsError,
  } = useWebSocket(currentUser, userKeys);

  // Fetch all users periodically
  const fetchUsers = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/users`);
      const data = await resp.json();
      setAllUsers(data.users || []);
    } catch (e) {
      console.error('Failed to fetch users:', e);
    }
  }, []);

  useEffect(() => {
    if (!currentUser) return;
    fetchUsers();
    const interval = setInterval(fetchUsers, 5000);
    return () => clearInterval(interval);
  }, [currentUser, fetchUsers]);

  // ---------- Persist keys helper ----------
  const persistKeys = (username, keys) => {
    sessionStorage.setItem('pqc_username', username);
    sessionStorage.setItem('pqc_keys', JSON.stringify(keys));
    localStorage.setItem(`pqc_keys_${username}`, JSON.stringify(keys));
  };

  // ---------- Firebase Auth Success Handler ----------
  const handleFirebaseAuthSuccess = (username, keys) => {
    setUserKeys(keys);
    setCurrentUser(username);
    persistKeys(username, keys);
  };

  // ---------- Local Sign Up ----------
  const handleSignup = async (e) => {
    e.preventDefault();
    const username = usernameInput.trim();
    const password = passwordInput;
    if (!username || !password) return;

    setLoginLoading(true);
    setLoginError('');

    try {
      const resp = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (resp.ok) {
        const data = await resp.json();
        const keys = {
          secret_key_kyber_hex: data.secret_key_kyber_hex,
          sign_key_dilithium_hex: data.sign_key_dilithium_hex,
        };
        setUserKeys(keys);
        setCurrentUser(username);
        persistKeys(username, keys);
      } else {
        const errData = await resp.json();
        setLoginError(
          errData.detail || 'Username already taken. Switch to "Log In" to re-authenticate.'
        );
      }
    } catch (e) {
      setLoginError('Cannot connect to server. Is the backend running on port 8000?');
    } finally {
      setLoginLoading(false);
    }
  };

  // ---------- Local Log In ----------
  const handleLogin = async (e) => {
    e.preventDefault();
    const username = usernameInput.trim();
    const password = passwordInput;
    if (!username || !password) return;

    setLoginLoading(true);
    setLoginError('');

    const savedKeysStr = localStorage.getItem(`pqc_keys_${username}`);
    if (!savedKeysStr) {
      setLoginError(
        'No saved keys found for this username on this device. If you registered on a different browser, you\'ll need to sign up again.'
      );
      setLoginLoading(false);
      return;
    }

    const savedKeys = JSON.parse(savedKeysStr);

    try {
      const resp = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          password,
          secret_key_kyber_hex: savedKeys.secret_key_kyber_hex,
          sign_key_dilithium_hex: savedKeys.sign_key_dilithium_hex,
        }),
      });

      if (resp.ok) {
        setUserKeys(savedKeys);
        setCurrentUser(username);
        persistKeys(username, savedKeys);
      } else {
        const errData = await resp.json();
        setLoginError(errData.detail || 'Login failed. Invalid password or keys.');
      }
    } catch (e) {
      setLoginError('Cannot connect to server. Is the backend running on port 8000?');
    } finally {
      setLoginLoading(false);
    }
  };

  // Handle logout
  const handleLogout = () => {
    sessionStorage.removeItem('pqc_username');
    sessionStorage.removeItem('pqc_keys');
    sessionStorage.removeItem('pqc_firebase_token');
    setCurrentUser(null);
    setUserKeys(null);
    setSelectedUser(null);
    setAllUsers([]);
    setPasswordInput('');
  };

  // Restore session on mount
  useEffect(() => {
    const savedUser = sessionStorage.getItem('pqc_username');
    const savedKeys = sessionStorage.getItem('pqc_keys');
    if (savedUser && savedKeys) {
      setCurrentUser(savedUser);
      setUserKeys(JSON.parse(savedKeys));
    }
  }, []);

  // ---- Login Screen ----
  if (!currentUser) {
    // Use Firebase auth if configured, otherwise local auth
    if (isFirebaseConfigured) {
      return <FirebaseAuth onAuthSuccess={handleFirebaseAuthSuccess} />;
    }

    return (
      <div className="login-screen" id="login-screen">
        <LoginThemeToggle />
        <form className="login-card" onSubmit={authMode === 'signup' ? handleSignup : handleLogin}>
          <h1>PQC Messenger</h1>
          <p className="subtitle">Post-Quantum Secure Messaging</p>

          <div className="algo-badges">
            <span className="algo-badge">🔑 Kyber512</span>
            <span className="algo-badge">✍️ ML-DSA-44</span>
            <span className="algo-badge">🔒 AES-256-GCM</span>
          </div>

          {/* Auth mode toggle */}
          <div className="auth-tabs">
            <button
              type="button"
              className={`auth-tab ${authMode === 'signup' ? 'active' : ''}`}
              onClick={() => { setAuthMode('signup'); setLoginError(''); }}
              id="tab-signup"
            >
              Sign Up
            </button>
            <button
              type="button"
              className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
              onClick={() => { setAuthMode('login'); setLoginError(''); }}
              id="tab-login"
            >
              Log In
            </button>
          </div>

          <div className="login-input-group">
            <label htmlFor="username-input">Username</label>
            <input
              id="username-input"
              type="text"
              placeholder={
                authMode === 'signup'
                  ? 'Choose a username (e.g., Alice)'
                  : 'Enter your existing username'
              }
              value={usernameInput}
              onChange={(e) => setUsernameInput(e.target.value)}
              autoFocus
              autoComplete="off"
            />
          </div>

          <div className="login-input-group">
            <label htmlFor="password-input">Password</label>
            <input
              id="password-input"
              type="password"
              placeholder={
                authMode === 'signup'
                  ? 'Create a password (min. 4 characters)'
                  : 'Enter your password'
              }
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              autoComplete={authMode === 'signup' ? 'new-password' : 'current-password'}
            />
          </div>

          <button
            type="submit"
            className="login-btn"
            disabled={!usernameInput.trim() || !passwordInput || passwordInput.length < 4 || loginLoading}
            id="login-btn"
          >
            {loginLoading
              ? (authMode === 'signup' ? 'Generating Keys...' : 'Verifying...')
              : (authMode === 'signup' ? '🔑 Generate Keys & Connect' : '🔐 Log In')
            }
          </button>

          {loginError && <p className="login-error">{loginError}</p>}

          <p className="login-hint">
            {authMode === 'signup' ? (
              <>
                A Kyber512 keypair and ML-DSA-44 signing keypair will be generated
                for you. Your private keys are saved locally in this browser.
              </>
            ) : (
              <>
                Your password will be verified against the server. Private keys
                are loaded from this browser's local storage. You must log in from
                the same browser you signed up on.
              </>
            )}
          </p>
        </form>
      </div>
    );
  }

  // ---- Main App ----
  return (
    <div className={`app-container ${!showVisualizer ? 'visualizer-hidden' : ''}`} id="app-container">
      {/* Sidebar — User List */}
      <UserList
        users={allUsers}
        usersOnline={usersOnline}
        currentUser={currentUser}
        selectedUser={selectedUser}
        onSelectUser={setSelectedUser}
        onLogout={handleLogout}
      />

      {/* Chat Area */}
      <div className="chat-area" id="chat-area">
        {/* Chat Header */}
        <div className="chat-header">
          <div className="chat-header-info">
            {selectedUser ? (
              <>
                <div className="user-avatar">
                  {selectedUser.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="chat-header-name">{selectedUser}</div>
                  <div className="chat-header-status">
                    <KeyExchangeStatus
                      selectedUser={selectedUser}
                      users={allUsers}
                      connected={connected}
                    />
                  </div>
                </div>
              </>
            ) : (
              <div className="chat-header-name" style={{ color: 'var(--text-muted)' }}>
                Select a conversation
              </div>
            )}
          </div>

          <button
            className={`visualizer-toggle ${showVisualizer ? 'active' : ''}`}
            onClick={() => setShowVisualizer(!showVisualizer)}
            id="visualizer-toggle"
          >
            🔬 {showVisualizer ? 'Hide' : 'Show'} Encryption Details
          </button>
        </div>

        {/* Messages */}
        <ChatWindow
          messages={messages}
          currentUser={currentUser}
          selectedUser={selectedUser}
        />

        {/* Input */}
        <MessageInput
          selectedUser={selectedUser}
          onSendMessage={sendMessage}
          disabled={!connected}
          currentUser={currentUser}
        />

        {/* Connection error banner */}
        {wsError && (
          <div style={{
            position: 'absolute',
            bottom: '80px',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '8px 20px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--accent-rose)',
            fontSize: '0.8rem',
            animation: 'fadeIn 0.3s ease',
            zIndex: 10,
          }}>
            ⚠️ {wsError}
          </div>
        )}
      </div>

      {/* Encryption Visualizer Panel */}
      {showVisualizer && (
        <EncryptionVisualizer
          cryptoTraces={cryptoTraces}
          onClear={clearTraces}
        />
      )}
    </div>
  );
}

export default App;
