"""
Module: backend.services.firestore_service
Purpose: Firestore integration for production data storage.
         Stores user profiles, public keys, message metadata, and media metadata.
         Encrypted payloads go to GCS (not Firestore) — Firestore holds only metadata.
Created by: TASK-27 (Phase 7 — Google Cloud Integration)

Collections:
  - users/{firebase_uid}      → email, public keys, created_at
  - messages/{message_id}     → sender, receiver, crypto metadata, GCS ref
  - media/{media_id}          → sender, receiver, file info, crypto metadata, GCS ref

Security model:
  - Public keys stored as hex strings (not binary) for Firestore compatibility
  - Plaintext message content is NEVER stored
  - Encrypted payloads are stored in GCS, referenced by storage_ref field
"""

import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature Flag
# ---------------------------------------------------------------------------
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "sqlite").lower()

# ---------------------------------------------------------------------------
# Firestore Client Initialization
# ---------------------------------------------------------------------------
_firestore_client = None


def _get_firestore_client():
    """Get or create the Firestore client (lazy initialization)."""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    try:
        from google.cloud import firestore

        project_id = os.environ.get("GCP_PROJECT_ID", os.environ.get("FIREBASE_PROJECT_ID"))
        _firestore_client = firestore.Client(project=project_id)
        logger.info(f"Firestore client initialized for project: {project_id}")
        return _firestore_client
    except Exception as e:
        logger.error(f"Failed to initialize Firestore client: {e}")
        raise


def is_firestore_enabled() -> bool:
    """Check if Firestore is the active storage backend."""
    return STORAGE_BACKEND == "firestore"


# ---------------------------------------------------------------------------
# User Operations
# ---------------------------------------------------------------------------
def save_user_firestore(
    uid: str,
    username: str,
    email: str,
    public_key_kyber_hex: str,
    public_key_dilithium_hex: str,
) -> dict:
    """
    Save a user profile and public keys to Firestore.

    Args:
        uid: Firebase UID (or generated ID for local dev).
        username: Display name / username.
        email: User's email address.
        public_key_kyber_hex: Kyber512 public key (hex-encoded).
        public_key_dilithium_hex: ML-DSA-44 public key (hex-encoded).

    Returns:
        dict with the saved user data.
    """
    db = _get_firestore_client()
    user_data = {
        "uid": uid,
        "username": username,
        "email": email,
        "public_key_kyber_hex": public_key_kyber_hex,
        "public_key_dilithium_hex": public_key_dilithium_hex,
        "created_at": datetime.now(timezone.utc),
    }
    db.collection("users").document(uid).set(user_data)
    logger.info(f"User saved to Firestore: {username} ({uid})")
    return user_data


def get_user_firestore(uid: str) -> dict | None:
    """
    Fetch a user profile from Firestore by UID.

    Returns:
        dict with user data, or None if not found.
    """
    db = _get_firestore_client()
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return None


def get_user_by_username_firestore(username: str) -> dict | None:
    """
    Fetch a user profile from Firestore by username.

    Returns:
        dict with user data, or None if not found.
    """
    db = _get_firestore_client()
    results = db.collection("users").where("username", "==", username).limit(1).stream()
    for doc in results:
        return doc.to_dict()
    return None


def list_users_firestore() -> list[dict]:
    """
    List all registered users from Firestore.

    Returns:
        List of user dicts with public info (no private keys).
    """
    db = _get_firestore_client()
    users = []
    for doc in db.collection("users").stream():
        data = doc.to_dict()
        users.append({
            "username": data.get("username", ""),
            "public_key_kyber_hex": data.get("public_key_kyber_hex", ""),
            "verify_key_dilithium_hex": data.get("public_key_dilithium_hex", ""),
            "created_at": data.get("created_at"),
        })
    return users


# ---------------------------------------------------------------------------
# Message Metadata Operations
# ---------------------------------------------------------------------------
def save_message_metadata_firestore(
    message_id: str,
    sender: str,
    receiver: str,
    storage_ref: str,
    kem_ciphertext_hex: str,
    nonce_hex: str,
    tag_hex: str,
    signature_hex: str,
) -> str:
    """
    Save message metadata to Firestore.
    The encrypted payload is stored in GCS; Firestore holds only metadata.

    Args:
        message_id: Unique message identifier.
        sender: Sender's username.
        receiver: Receiver's username.
        storage_ref: GCS object path for the encrypted payload.
        kem_ciphertext_hex: Kyber KEM ciphertext (hex).
        nonce_hex: AES-GCM nonce (hex).
        tag_hex: AES-GCM auth tag (hex).
        signature_hex: ML-DSA-44 signature (hex).

    Returns:
        The message_id.
    """
    db = _get_firestore_client()
    msg_data = {
        "message_id": message_id,
        "sender": sender,
        "receiver": receiver,
        "storage_ref": storage_ref,
        "kem_ciphertext_hex": kem_ciphertext_hex,
        "nonce_hex": nonce_hex,
        "tag_hex": tag_hex,
        "signature_hex": signature_hex,
        "timestamp": datetime.now(timezone.utc),
    }
    db.collection("messages").document(message_id).set(msg_data)
    return message_id


def get_messages_firestore(user_a: str, user_b: str) -> list[dict]:
    """
    Retrieve message metadata between two users from Firestore.
    Returns messages in both directions, ordered by timestamp.
    """
    db = _get_firestore_client()
    messages = []

    # Query both directions
    for sender, receiver in [(user_a, user_b), (user_b, user_a)]:
        query = (
            db.collection("messages")
            .where("sender", "==", sender)
            .where("receiver", "==", receiver)
            .stream()
        )
        for doc in query:
            data = doc.to_dict()
            messages.append({
                "id": data.get("message_id", doc.id),
                "sender": data["sender"],
                "receiver": data["receiver"],
                "storage_ref": data.get("storage_ref", ""),
                "ciphertext_hex": "",  # Stored in GCS, not Firestore
                "nonce_hex": data.get("nonce_hex", ""),
                "tag_hex": data.get("tag_hex", ""),
                "signature_hex": data.get("signature_hex", ""),
                "kem_ciphertext_hex": data.get("kem_ciphertext_hex", ""),
                "timestamp": data.get("timestamp"),
            })

    # Sort by timestamp
    messages.sort(key=lambda m: m.get("timestamp") or datetime.min.replace(tzinfo=timezone.utc))
    return messages


# ---------------------------------------------------------------------------
# Media Metadata Operations
# ---------------------------------------------------------------------------
def save_media_metadata_firestore(
    media_id: str,
    sender: str,
    receiver: str,
    file_type: str,
    original_filename: str,
    file_size_bytes: int,
    storage_ref: str,
    nonce_hex: str,
    tag_hex: str,
    kem_ciphertext_hex: str,
    signature_hex: str,
) -> str:
    """
    Save media file metadata to Firestore.
    Encrypted file bytes are stored in GCS.
    """
    db = _get_firestore_client()
    media_data = {
        "media_id": media_id,
        "sender": sender,
        "receiver": receiver,
        "file_type": file_type,
        "original_filename": original_filename,
        "file_size_bytes": file_size_bytes,
        "storage_ref": storage_ref,
        "nonce_hex": nonce_hex,
        "tag_hex": tag_hex,
        "kem_ciphertext_hex": kem_ciphertext_hex,
        "signature_hex": signature_hex,
        "timestamp": datetime.now(timezone.utc),
    }
    db.collection("media").document(media_id).set(media_data)
    return media_id


def get_media_metadata_firestore(media_id: str) -> dict | None:
    """Fetch media metadata from Firestore by ID."""
    db = _get_firestore_client()
    doc = db.collection("media").document(media_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def get_media_history_firestore(user_a: str, user_b: str) -> list[dict]:
    """Retrieve media metadata between two users from Firestore."""
    db = _get_firestore_client()
    media_list = []

    for sender, receiver in [(user_a, user_b), (user_b, user_a)]:
        query = (
            db.collection("media")
            .where("sender", "==", sender)
            .where("receiver", "==", receiver)
            .stream()
        )
        for doc in query:
            data = doc.to_dict()
            media_list.append({
                "id": data.get("media_id", doc.id),
                "sender": data["sender"],
                "receiver": data["receiver"],
                "file_type": data.get("file_type", ""),
                "original_filename": data.get("original_filename", ""),
                "file_size_bytes": data.get("file_size_bytes", 0),
                "timestamp": data.get("timestamp"),
            })

    media_list.sort(key=lambda m: m.get("timestamp") or datetime.min.replace(tzinfo=timezone.utc))
    return media_list
