/**
 * Module: frontend/src/components/FirebaseAuth.jsx
 * Purpose: Firebase email/password authentication UI component.
 *          Replaces the default login card when Firebase is configured.
 *          After Firebase auth, calls backend /auth/register or /auth/login
 *          with the Firebase ID token to generate/verify PQC keypairs.
 * Created by: TASK-26 (Phase 7 — Google Cloud Integration)
 */

import { useState } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
} from 'firebase/auth';
import { auth, isFirebaseConfigured } from '../services/firebaseConfig';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export function FirebaseAuth({ onAuthSuccess }) {
  const [authMode, setAuthMode] = useState('signup');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) return;
    if (authMode === 'signup' && !username.trim()) return;

    setLoading(true);
    setError('');

    try {
      let userCredential;

      if (authMode === 'signup') {
        // Step 1: Create Firebase user
        userCredential = await createUserWithEmailAndPassword(auth, email, password);
      } else {
        // Step 1: Sign in with Firebase
        userCredential = await signInWithEmailAndPassword(auth, email, password);
      }

      // Step 2: Get Firebase ID token
      const idToken = await userCredential.user.getIdToken();

      if (authMode === 'signup') {
        // Step 3a: Register with backend — generates PQC keypairs
        const resp = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            firebase_id_token: idToken,
            username: username.trim(),
          }),
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.detail || 'Registration failed');
        }

        const data = await resp.json();
        const keys = {
          secret_key_kyber_hex: data.secret_key_kyber_hex,
          sign_key_dilithium_hex: data.sign_key_dilithium_hex,
        };

        // Save keys locally
        const displayName = data.username;
        localStorage.setItem(`pqc_keys_${displayName}`, JSON.stringify(keys));
        sessionStorage.setItem('pqc_username', displayName);
        sessionStorage.setItem('pqc_keys', JSON.stringify(keys));
        sessionStorage.setItem('pqc_firebase_token', idToken);

        onAuthSuccess(displayName, keys);
      } else {
        // Step 3b: Login — load saved PQC keys and verify
        // Try to find saved keys by checking email-based or username-based storage
        const savedUsername = localStorage.getItem(`pqc_firebase_user_${userCredential.user.uid}`);
        if (!savedUsername) {
          throw new Error('No PQC keys found for this Firebase account on this device. Please sign up again.');
        }

        const savedKeysStr = localStorage.getItem(`pqc_keys_${savedUsername}`);
        if (!savedKeysStr) {
          throw new Error('No saved PQC keys found. Please sign up again on this device.');
        }

        const savedKeys = JSON.parse(savedKeysStr);

        const resp = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            firebase_id_token: idToken,
            secret_key_kyber_hex: savedKeys.secret_key_kyber_hex,
            sign_key_dilithium_hex: savedKeys.sign_key_dilithium_hex,
          }),
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.detail || 'Login failed');
        }

        sessionStorage.setItem('pqc_username', savedUsername);
        sessionStorage.setItem('pqc_keys', JSON.stringify(savedKeys));
        sessionStorage.setItem('pqc_firebase_token', idToken);

        onAuthSuccess(savedUsername, savedKeys);
      }
    } catch (err) {
      // Firebase-specific error messages
      const firebaseErrors = {
        'auth/email-already-in-use': 'Email already registered. Switch to Log In.',
        'auth/invalid-email': 'Invalid email address.',
        'auth/weak-password': 'Password must be at least 6 characters.',
        'auth/user-not-found': 'No account found with this email.',
        'auth/wrong-password': 'Incorrect password.',
        'auth/invalid-credential': 'Invalid credentials. Check your email and password.',
      };
      const code = err.code || '';
      setError(firebaseErrors[code] || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Save username → Firebase UID mapping on signup for login retrieval
  const handleSignupSuccess = (username, firebaseUid) => {
    localStorage.setItem(`pqc_firebase_user_${firebaseUid}`, username);
  };

  return (
    <div className="login-screen" id="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>PQC Messenger</h1>
        <p className="subtitle">Post-Quantum Secure Messaging</p>

        <div className="algo-badges">
          <span className="algo-badge">🔑 Kyber512</span>
          <span className="algo-badge">✍️ ML-DSA-44</span>
          <span className="algo-badge">🔒 AES-256-GCM</span>
        </div>

        {/* Google Cloud badge */}
        <div style={{
          textAlign: 'center',
          marginBottom: '20px',
        }}>
          <span className="algo-badge" style={{
            background: 'rgba(52, 211, 153, 0.12)',
            borderColor: 'rgba(52, 211, 153, 0.25)',
            color: 'var(--accent-emerald)',
          }}>
            ☁️ Powered by Google Cloud
          </span>
        </div>

        {/* Auth mode toggle */}
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${authMode === 'signup' ? 'active' : ''}`}
            onClick={() => { setAuthMode('signup'); setError(''); }}
            id="tab-signup"
          >
            Sign Up
          </button>
          <button
            type="button"
            className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
            onClick={() => { setAuthMode('login'); setError(''); }}
            id="tab-login"
          >
            Log In
          </button>
        </div>

        {authMode === 'signup' && (
          <div className="login-input-group">
            <label htmlFor="username-input">Username</label>
            <input
              id="username-input"
              type="text"
              placeholder="Choose a display name (e.g., Alice)"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="off"
            />
          </div>
        )}

        <div className="login-input-group">
          <label htmlFor="email-input">Email</label>
          <input
            id="email-input"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
            autoComplete="email"
          />
        </div>

        <div className="login-input-group">
          <label htmlFor="password-input">Password</label>
          <input
            id="password-input"
            type="password"
            placeholder={
              authMode === 'signup'
                ? 'Create a password (min. 6 characters)'
                : 'Enter your password'
            }
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={authMode === 'signup' ? 'new-password' : 'current-password'}
          />
        </div>

        <button
          type="submit"
          className="login-btn"
          disabled={
            !email || !password || password.length < 6 ||
            (authMode === 'signup' && !username.trim()) ||
            loading
          }
          id="login-btn"
        >
          {loading
            ? (authMode === 'signup' ? 'Generating Keys...' : 'Verifying...')
            : (authMode === 'signup' ? '🔑 Generate Keys & Connect' : '🔐 Log In')
          }
        </button>

        {error && <p className="login-error">{error}</p>}

        <p className="login-hint">
          {authMode === 'signup' ? (
            <>
              Authenticated via Firebase. A Kyber512 keypair and ML-DSA-44
              signing keypair will be generated for you. Private keys are saved
              locally in this browser.
            </>
          ) : (
            <>
              Sign in with your Firebase account. PQC private keys are loaded
              from this browser&apos;s local storage. You must log in from the
              same browser you signed up on.
            </>
          )}
        </p>

        <div style={{
          textAlign: 'center',
          marginTop: '12px',
          fontSize: '0.65rem',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
        }}>
          Firebase Auth → Kyber512 KEM → AES-256-GCM → ML-DSA-44
        </div>
      </form>
    </div>
  );
}
