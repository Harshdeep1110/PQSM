"""
Module: backend.services.gcs_service
Purpose: Google Cloud Storage integration for encrypted data at rest.
         Stores encrypted message payloads and media files as GCS objects.
         Even if GCS is breached, data is quantum-safe encrypted (Kyber512 + AES-256-GCM).
Created by: TASK-28 (Phase 7 — Google Cloud Integration)

Bucket structure:
  - messages/{message_id}.enc   → encrypted message ciphertext
  - media/{media_id}.enc       → encrypted media file bytes

Security model:
  - ALL objects are AES-256-GCM encrypted BEFORE upload
  - Objects are Kyber512 KEM-wrapped — quantum-safe
  - A breach of the GCS bucket yields only encrypted blobs
"""

import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "pqsm-18197-encrypted-data")
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "sqlite").lower()

# ---------------------------------------------------------------------------
# GCS Client Initialization
# ---------------------------------------------------------------------------
_gcs_client = None
_gcs_bucket = None


def _get_gcs_bucket():
    """Get or create the GCS bucket reference (lazy initialization)."""
    global _gcs_client, _gcs_bucket
    if _gcs_bucket is not None:
        return _gcs_bucket

    try:
        from google.cloud import storage

        project_id = os.environ.get("GCP_PROJECT_ID")
        _gcs_client = storage.Client(project=project_id)
        _gcs_bucket = _gcs_client.bucket(GCS_BUCKET_NAME)
        logger.info(f"GCS client initialized for bucket: {GCS_BUCKET_NAME}")
        return _gcs_bucket
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        raise


def is_gcs_enabled() -> bool:
    """Check if GCS storage is enabled (Firestore mode implies GCS for blobs)."""
    return STORAGE_BACKEND == "firestore"


# ---------------------------------------------------------------------------
# Message Payload Operations
# ---------------------------------------------------------------------------
def upload_encrypted_message(message_id: str, encrypted_bytes: bytes) -> str:
    """
    Upload an encrypted message payload to GCS.

    Args:
        message_id: Unique message identifier.
        encrypted_bytes: AES-256-GCM encrypted ciphertext (already quantum-safe).

    Returns:
        GCS object path (e.g., "messages/abc123.enc").
    """
    bucket = _get_gcs_bucket()
    object_path = f"messages/{message_id}.enc"
    blob = bucket.blob(object_path)
    blob.upload_from_string(encrypted_bytes, content_type="application/octet-stream")
    logger.info(f"Encrypted message uploaded to GCS: {object_path} ({len(encrypted_bytes)} bytes)")
    return object_path


def download_encrypted_message(message_id: str) -> bytes:
    """
    Download an encrypted message payload from GCS.

    Args:
        message_id: The message identifier.

    Returns:
        Raw encrypted bytes.

    Raises:
        FileNotFoundError: If the object doesn't exist.
    """
    bucket = _get_gcs_bucket()
    object_path = f"messages/{message_id}.enc"
    blob = bucket.blob(object_path)

    if not blob.exists():
        raise FileNotFoundError(f"Encrypted message not found in GCS: {object_path}")

    return blob.download_as_bytes()


# ---------------------------------------------------------------------------
# Media File Operations
# ---------------------------------------------------------------------------
def upload_encrypted_media(media_id: str, encrypted_bytes: bytes) -> str:
    """
    Upload an encrypted media file to GCS.

    Args:
        media_id: Unique media identifier (UUID).
        encrypted_bytes: AES-256-GCM encrypted file bytes.

    Returns:
        GCS object path (e.g., "media/uuid.enc").
    """
    bucket = _get_gcs_bucket()
    object_path = f"media/{media_id}.enc"
    blob = bucket.blob(object_path)
    blob.upload_from_string(encrypted_bytes, content_type="application/octet-stream")
    logger.info(f"Encrypted media uploaded to GCS: {object_path} ({len(encrypted_bytes)} bytes)")
    return object_path


def download_encrypted_media(media_id: str) -> bytes:
    """
    Download an encrypted media file from GCS.

    Args:
        media_id: The media file identifier.

    Returns:
        Raw encrypted bytes.

    Raises:
        FileNotFoundError: If the object doesn't exist.
    """
    bucket = _get_gcs_bucket()
    object_path = f"media/{media_id}.enc"
    blob = bucket.blob(object_path)

    if not blob.exists():
        raise FileNotFoundError(f"Encrypted media not found in GCS: {object_path}")

    return blob.download_as_bytes()


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
def delete_object(object_path: str) -> bool:
    """
    Delete an object from GCS.

    Args:
        object_path: Full object path (e.g., "messages/abc.enc").

    Returns:
        True if deleted, False if not found.
    """
    try:
        bucket = _get_gcs_bucket()
        blob = bucket.blob(object_path)
        if blob.exists():
            blob.delete()
            logger.info(f"GCS object deleted: {object_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete GCS object {object_path}: {e}")
        return False
