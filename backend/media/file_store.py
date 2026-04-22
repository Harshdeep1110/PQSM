"""
Module: backend.media.file_store
Purpose: Database operations for media file records.
         Stores and retrieves metadata for encrypted media files.
Created by: TASK-17

The server stores only encrypted bytes — plaintext file content is NEVER written to disk.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.database import MediaFileRecord


# ---------------------------------------------------------------------------
# Save Media Record
# ---------------------------------------------------------------------------
def save_media_record(
    db: Session,
    sender: str,
    receiver: str,
    file_type: str,
    original_filename: str,
    stored_filename: str,
    encrypted_path: str,
    file_size_bytes: int,
    nonce_hex: str,
    tag_hex: str,
    kem_ciphertext_hex: str,
    signature_hex: str,
) -> str:
    """
    Save a media file record to the database.

    Args:
        db: SQLAlchemy database session.
        sender: Sender's username.
        receiver: Receiver's username.
        file_type: File category (image, video, audio, document).
        original_filename: Sanitized original filename.
        stored_filename: UUID-based filename on disk.
        encrypted_path: Relative path under uploads/.
        file_size_bytes: Original file size in bytes.
        nonce_hex: AES-GCM nonce (hex-encoded).
        tag_hex: AES-GCM authentication tag (hex-encoded).
        kem_ciphertext_hex: Kyber KEM ciphertext (hex-encoded).
        signature_hex: Dilithium signature (hex-encoded).

    Returns:
        The generated media_id (UUID string).
    """
    media_id = str(uuid.uuid4())

    record = MediaFileRecord(
        id=media_id,
        sender=sender,
        receiver=receiver,
        file_type=file_type,
        original_filename=original_filename,
        stored_filename=stored_filename,
        encrypted_path=encrypted_path,
        file_size_bytes=file_size_bytes,
        nonce_hex=nonce_hex,
        tag_hex=tag_hex,
        kem_ciphertext_hex=kem_ciphertext_hex,
        signature_hex=signature_hex,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return media_id


# ---------------------------------------------------------------------------
# Get Media Record
# ---------------------------------------------------------------------------
def get_media_record(db: Session, media_id: str) -> MediaFileRecord | None:
    """
    Fetch a single media file record by ID.

    Args:
        db: SQLAlchemy database session.
        media_id: UUID of the media file.

    Returns:
        MediaFileRecord or None if not found.
    """
    return db.query(MediaFileRecord).filter(MediaFileRecord.id == media_id).first()


# ---------------------------------------------------------------------------
# Get Media History
# ---------------------------------------------------------------------------
def get_media_history(db: Session, user_a: str, user_b: str) -> list[dict]:
    """
    Retrieve media file history between two users.

    Returns media records in both directions (A→B and B→A), ordered by timestamp.

    Args:
        db: SQLAlchemy database session.
        user_a: First user's username.
        user_b: Second user's username.

    Returns:
        List of media file record dicts.
    """
    records = (
        db.query(MediaFileRecord)
        .filter(
            (
                (MediaFileRecord.sender == user_a) & (MediaFileRecord.receiver == user_b)
            )
            | (
                (MediaFileRecord.sender == user_b) & (MediaFileRecord.receiver == user_a)
            )
        )
        .order_by(MediaFileRecord.timestamp.asc())
        .all()
    )

    return [
        {
            "id": r.id,
            "sender": r.sender,
            "receiver": r.receiver,
            "file_type": r.file_type,
            "original_filename": r.original_filename,
            "file_size_bytes": r.file_size_bytes,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in records
    ]
