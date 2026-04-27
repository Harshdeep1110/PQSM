"""
Module: backend.services.audit_logger
Purpose: Cloud Logging integration for cryptographic audit trail.
         Logs all crypto events (key gen, encrypt, decrypt, sign, verify)
         to Google Cloud Logging for auditability and demo purposes.
Created by: TASK-30 (Phase 7)

Each log entry includes:
  - event_type: key_generation, kem_encapsulation, kem_decapsulation,
                aes_encrypt, aes_decrypt, signature_sign, signature_verify
  - algorithm: Kyber512, AES-256-GCM, ML-DSA-44
  - user_id_hash: SHA-256 of the user ID (privacy-preserving)
  - timestamp, success/fail, duration_ms
"""

import os
import time
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

ENABLE_AUDIT_LOGGING = os.environ.get("ENABLE_AUDIT_LOGGING", "false").lower() == "true"
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "pqsm-18197")
AUDIT_LOG_NAME = "pqc-crypto-audit"

_cloud_logger = None
# In-memory cache for the audit log panel (last 200 entries)
_recent_logs: list[dict] = []
MAX_RECENT_LOGS = 200


def _get_cloud_logger():
    global _cloud_logger
    if _cloud_logger is not None:
        return _cloud_logger
    if not ENABLE_AUDIT_LOGGING:
        return None
    try:
        import google.cloud.logging as cloud_logging
        client = cloud_logging.Client(project=GCP_PROJECT_ID)
        _cloud_logger = client.logger(AUDIT_LOG_NAME)
        logger.info(f"Cloud Logging initialized: {AUDIT_LOG_NAME}")
        return _cloud_logger
    except Exception as e:
        logger.warning(f"Cloud Logging unavailable (local mode): {e}")
        return None


def _hash_user_id(user_id: str) -> str:
    """Hash a user ID for privacy-preserving logging."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def log_crypto_event(
    event_type: str,
    algorithm: str,
    user_id: str,
    success: bool = True,
    duration_ms: float = 0,
    metadata: dict = None,
):
    """
    Log a cryptographic event to Cloud Logging and the in-memory cache.

    Args:
        event_type: e.g., 'kem_encapsulation', 'aes_encrypt', 'signature_sign'
        algorithm: e.g., 'Kyber512', 'AES-256-GCM', 'ML-DSA-44'
        user_id: The user performing the operation (will be hashed).
        success: Whether the operation succeeded.
        duration_ms: Operation duration in milliseconds.
        metadata: Optional additional data.
    """
    entry = {
        "event_type": event_type,
        "algorithm": algorithm,
        "user_id_hash": _hash_user_id(user_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "duration_ms": round(duration_ms, 2),
    }
    if metadata:
        entry["metadata"] = metadata

    # Add to in-memory cache
    _recent_logs.append(entry)
    if len(_recent_logs) > MAX_RECENT_LOGS:
        _recent_logs.pop(0)

    # Log to Cloud Logging if enabled
    cloud_log = _get_cloud_logger()
    if cloud_log:
        try:
            cloud_log.log_struct(entry, severity="INFO" if success else "WARNING")
        except Exception as e:
            logger.debug(f"Cloud Logging write failed: {e}")

    # Always log locally
    status = "✓" if success else "✗"
    logger.info(f"[AUDIT] {status} {event_type} | {algorithm} | user={entry['user_id_hash']} | {duration_ms:.1f}ms")


def get_recent_logs(limit: int = 50) -> list[dict]:
    """
    Get recent audit log entries from the in-memory cache.
    Used by the GET /audit/logs endpoint for the frontend panel.

    Args:
        limit: Max number of entries to return.

    Returns:
        List of audit log entries, newest first.
    """
    return list(reversed(_recent_logs[-limit:]))


class CryptoTimer:
    """Context manager for timing crypto operations and logging them."""

    def __init__(self, event_type: str, algorithm: str, user_id: str, metadata: dict = None):
        self.event_type = event_type
        self.algorithm = algorithm
        self.user_id = user_id
        self.metadata = metadata
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        success = exc_type is None
        log_crypto_event(
            event_type=self.event_type,
            algorithm=self.algorithm,
            user_id=self.user_id,
            success=success,
            duration_ms=duration_ms,
            metadata=self.metadata,
        )
        return False  # Don't suppress exceptions
