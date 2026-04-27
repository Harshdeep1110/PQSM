"""
Module: backend.media.file_store
Purpose: Database operations for media file records.
         Stores and retrieves metadata for encrypted media files.
         Supports both SQLite (local dev) and Firestore (production).
Created by: TASK-17, Modified for Firestore support
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
    Save a media file record to the database (Firestore or SQLite).
    Returns the generated media_id (UUID string).
    """
    from backend.services.firestore_service import is_firestore_enabled

    media_id = str(uuid.uuid4())

    if is_firestore_enabled():
        from backend.services.firestore_service import save_media_metadata_firestore
        save_media_metadata_firestore(
            media_id=media_id,
            sender=sender,
            receiver=receiver,
            file_type=file_type,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            storage_ref=encrypted_path,
            nonce_hex=nonce_hex,
            tag_hex=tag_hex,
            kem_ciphertext_hex=kem_ciphertext_hex,
            signature_hex=signature_hex,
        )
        # Also store stored_filename so we can retrieve from GCS later
        from backend.services.firestore_service import _get_firestore_client
        fs = _get_firestore_client()
        fs.collection("media").document(media_id).update({
            "stored_filename": stored_filename,
            "encrypted_path": encrypted_path,
        })
        return media_id

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
def get_media_record(db: Session, media_id: str):
    """
    Fetch a single media file record by ID (Firestore or SQLite).
    Returns a MediaFileRecord or a Firestore proxy object, or None.
    """
    from backend.services.firestore_service import is_firestore_enabled

    if is_firestore_enabled():
        from backend.services.firestore_service import get_media_metadata_firestore
        data = get_media_metadata_firestore(media_id)
        if data:
            class FirestoreMediaProxy:
                def __init__(self, d):
                    self.id = d.get("media_id", media_id)
                    self.sender = d["sender"]
                    self.receiver = d["receiver"]
                    self.file_type = d.get("file_type", "")
                    self.original_filename = d.get("original_filename", "")
                    self.stored_filename = d.get("stored_filename", "")
                    self.encrypted_path = d.get("encrypted_path", d.get("storage_ref", ""))
                    self.file_size_bytes = d.get("file_size_bytes", 0)
                    self.nonce_hex = d.get("nonce_hex", "")
                    self.tag_hex = d.get("tag_hex", "")
                    self.kem_ciphertext_hex = d.get("kem_ciphertext_hex", "")
                    self.signature_hex = d.get("signature_hex", "")
                    self.timestamp = d.get("timestamp")
            return FirestoreMediaProxy(data)
        return None

    return db.query(MediaFileRecord).filter(MediaFileRecord.id == media_id).first()


# ---------------------------------------------------------------------------
# Get Media History
# ---------------------------------------------------------------------------
def get_media_history(db: Session, user_a: str, user_b: str) -> list[dict]:
    """
    Retrieve media file history between two users (Firestore or SQLite).
    """
    from backend.services.firestore_service import is_firestore_enabled

    if is_firestore_enabled():
        from backend.services.firestore_service import get_media_history_firestore
        return get_media_history_firestore(user_a, user_b)

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
