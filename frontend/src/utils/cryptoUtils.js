/**
 * Module: frontend/src/utils/cryptoUtils.js
 * Purpose: Utility functions for displaying crypto data in the UI.
 * Created by: TASK-09
 */

/**
 * Truncate a hex string for display purposes.
 * Shows the first N characters followed by "..."
 *
 * @param {string} hexString - Full hex-encoded string
 * @param {number} showChars - Number of hex characters to show (default: 16)
 * @returns {string} Truncated hex string
 */
export function formatHex(hexString, showChars = 16) {
  if (!hexString) return '(empty)';
  if (hexString.length <= showChars) return hexString;
  return hexString.substring(0, showChars) + '...';
}

/**
 * Format a byte count into a human-readable string.
 * @param {number} bytes
 * @returns {string}
 */
export function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

/**
 * Calculate byte length from a hex string.
 * @param {string} hexString
 * @returns {number}
 */
export function hexToByteLength(hexString) {
  if (!hexString) return 0;
  return Math.floor(hexString.length / 2);
}

/**
 * Format a timestamp for display.
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string}
 */
export function formatTimestamp(isoString) {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}
