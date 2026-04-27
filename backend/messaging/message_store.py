"""
Module: backend.messaging.message_store
Purpose: Encrypted message persistence using SQLite or Firestore.
         Stores and retrieves encrypted messages — the server NEVER handles plaintext.
Created by: TASK-06, Modified for Firestore support

All messages are stored in their encrypted form (hex-encoded ciphertext, nonce, tag,
signature, and KEM ciphertext). Decryption happens client-side or in the WebSocket
handler when delivering to the recipient.
"""

import uuid
from sqlalchemy.orm import Session
from backend.database import MessageRecord


# ---------------------------------------------------------------------------
# Save Message
# ---------------------------------------------------------------------------
def save_message(
    db: Session,
    sender: str,
    receiver: str,
    ciphertext_hex: str,
    nonce_hex: str,
    tag_hex: str,
    signature_hex: str,
    kem_ciphertext_hex: str = "",
) -> MessageRecord | str:
    """
    Persist an encrypted message to the database (Firestore or SQLite).
    All data is stored in encrypted form — plaintext is NEVER written to disk.

    Returns:
        The saved MessageRecord (SQLite) or message_id string (Firestore).
    """
    from backend.services.firestore_service import is_firestore_enabled

    if is_firestore_enabled():
        from backend.services.firestore_service import save_message_metadata_firestore
        message_id = str(uuid.uuid4())
        save_message_metadata_firestore(
            message_id=message_id,
            sender=sender,
            receiver=receiver,
            storage_ref="",
            kem_ciphertext_hex=kem_ciphertext_hex,
            nonce_hex=nonce_hex,
            tag_hex=tag_hex,
            signature_hex=signature_hex,
        )
        return message_id

    msg = MessageRecord(
        sender=sender,
        receiver=receiver,
        ciphertext=ciphertext_hex,
        nonce=nonce_hex,
        tag=tag_hex,
        signature=signature_hex,
        kem_ciphertext=kem_ciphertext_hex,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# ---------------------------------------------------------------------------
# Get Message History
# ---------------------------------------------------------------------------
def get_messages(db: Session, user_a: str, user_b: str) -> list[dict]:
    """
    Retrieve encrypted message history between two users (Firestore or SQLite).
    Returns messages in both directions (A→B and B→A), ordered by timestamp.
    """
    from backend.services.firestore_service import is_firestore_enabled

    if is_firestore_enabled():
        from backend.services.firestore_service import get_messages_firestore
        return get_messages_firestore(user_a, user_b)

    messages = (
        db.query(MessageRecord)
        .filter(
            (
                (MessageRecord.sender == user_a) & (MessageRecord.receiver == user_b)
            )
            | (
                (MessageRecord.sender == user_b) & (MessageRecord.receiver == user_a)
            )
        )
        .order_by(MessageRecord.timestamp.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "sender": m.sender,
            "receiver": m.receiver,
            "ciphertext_hex": m.ciphertext,
            "nonce_hex": m.nonce,
            "tag_hex": m.tag,
            "signature_hex": m.signature,
            "kem_ciphertext_hex": m.kem_ciphertext,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        }
        for m in messages
    ]
