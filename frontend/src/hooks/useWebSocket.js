/**
 * Module: frontend/src/hooks/useWebSocket.js
 * Purpose: React hook for WebSocket connection to the PQC Messenger backend.
 *          Manages connection state, message sending/receiving, and crypto traces.
 * Created by: TASK-09
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_BACKEND_WS_URL
  ? `${import.meta.env.VITE_BACKEND_WS_URL}/ws`
  : 'ws://localhost:8000/ws';

/**
 * Custom hook for managing WebSocket connections.
 *
 * @param {string} username - The authenticated username
 * @param {object} keys - User's private keys { secret_key_kyber_hex, sign_key_dilithium_hex }
 * @returns {object} { connected, messages, cryptoTraces, usersOnline, sendMessage, error }
 */
export function useWebSocket(username, keys) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [cryptoTraces, setCryptoTraces] = useState([]);
  const [usersOnline, setUsersOnline] = useState([]);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Connect to WebSocket
  useEffect(() => {
    if (!username || !keys) return;

    const connect = () => {
      try {
        const ws = new WebSocket(`${WS_BASE_URL}/${username}`);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          setError(null);

          // Send authentication message with private keys
          ws.send(JSON.stringify({
            type: 'auth',
            secret_key_kyber_hex: keys.secret_key_kyber_hex,
            sign_key_dilithium_hex: keys.sign_key_dilithium_hex,
          }));

          // Start heartbeat to keep connection alive and detect dropped connections
          window.pqcPingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ping' }));
            }
          }, 20000); // 20 seconds
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleMessage(data);
          } catch (e) {
            console.error('Failed to parse WS message:', e);
          }
        };

        ws.onclose = () => {
          setConnected(false);
          if (window.pqcPingInterval) clearInterval(window.pqcPingInterval);
          // Attempt reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        };

        ws.onerror = (e) => {
          console.error('WebSocket error:', e);
          setError('Connection error');
        };
      } catch (e) {
        console.error('Failed to create WebSocket:', e);
        setError('Failed to connect');
      }
    };

    connect();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [username, keys]);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'auth_success':
        setUsersOnline(data.users_online || []);
        break;

      case 'user_list':
        setUsersOnline(data.users_online || []);
        break;

      case 'decrypted_message':
        // Received a decrypted message from another user
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          sender: data.sender,
          receiver: data.receiver || username,
          plaintext: data.plaintext,
          direction: 'received',
          signatureValid: data.signature_valid,
          timestamp: data.timestamp,
        }]);
        break;

      case 'crypto_trace':
        // Crypto trace for the Encryption Visualizer
        setCryptoTraces(prev => [...prev, {
          id: Date.now() + Math.random(),
          ...data,
        }]);
        break;

      case 'media_message':
        // Received a media file notification from another user
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'media_message',
          media_id: data.media_id,
          sender: data.sender,
          receiver: data.receiver || username,
          file_type: data.file_type,
          original_filename: data.original_filename,
          file_size_bytes: data.file_size_bytes,
          direction: 'received',
          timestamp: data.timestamp || new Date().toISOString(),
        }]);
        break;

      case 'media_crypto_trace':
        // Media-specific crypto trace for the Encryption Visualizer
        setCryptoTraces(prev => [...prev, {
          id: Date.now() + Math.random(),
          ...data,
        }]);
        break;

      case 'message_sent':
        // Confirmation that message was sent successfully
        break;

      case 'encrypted_message':
        // Fallback: received encrypted message (couldn't decrypt server-side)
        setMessages(prev => [...prev, {
          id: Date.now() + Math.random(),
          sender: data.sender,
          plaintext: '[Encrypted — unable to decrypt]',
          direction: 'received',
          encrypted: true,
          timestamp: new Date().toISOString(),
        }]);
        break;

      case 'error':
        setError(data.message);
        break;

      case 'pong':
        break;

      default:
        console.log('Unknown WS message type:', data.type);
    }
  }, []);

  // Send a chat message
  const sendMessage = useCallback((to, plaintext) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected');
      return false;
    }

    // Add the message to local state immediately (optimistic UI)
    setMessages(prev => [...prev, {
      id: Date.now() + Math.random(),
      sender: username,
      receiver: to,
      plaintext: plaintext,
      direction: 'sent',
      timestamp: new Date().toISOString(),
    }]);

    // Send to server for encryption and forwarding
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      to: to,
      plaintext: plaintext,
    }));

    return true;
  }, [username]);

  // Clear crypto traces
  const clearTraces = useCallback(() => {
    setCryptoTraces([]);
  }, []);

  return {
    connected,
    messages,
    setMessages,
    cryptoTraces,
    usersOnline,
    sendMessage,
    clearTraces,
    error,
  };
}
