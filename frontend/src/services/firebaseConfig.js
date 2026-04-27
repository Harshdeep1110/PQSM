/**
 * Module: frontend/src/services/firebaseConfig.js
 * Purpose: Firebase JS SDK initialization and configuration.
 *          Provides Firebase Auth instance for email/password authentication.
 * Created by: TASK-26 (Phase 7 — Google Cloud Integration)
 *
 * Configuration values come from Vite environment variables (VITE_ prefix).
 * Set these in your .env.local or in the hosting platform's env vars.
 */

import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Firebase project configuration
// These values are NOT secrets — they are safe to include in client-side code.
// Firebase Security Rules protect backend access, not these config values.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'pqsm-18197.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'pqsm-18197',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'pqsm-18197.appspot.com',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
};

// Check if Firebase is configured
export const isFirebaseConfigured = Boolean(firebaseConfig.apiKey);

// Initialize Firebase app
let app = null;
let auth = null;

if (isFirebaseConfigured) {
  try {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    console.log('[Firebase] Initialized for project:', firebaseConfig.projectId);
  } catch (e) {
    console.warn('[Firebase] Initialization failed:', e.message);
  }
}

export { app, auth };
export default firebaseConfig;
