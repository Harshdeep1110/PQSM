"""
Module: backend.messaging.message_store
Purpose: Encrypted message persistence using SQLite.
         Stores and retrieves encrypted messages — the server NEVER handles plaintext.
Created by: TASK-06

All messages are stored in their encrypted form (hex-encoded ciphertext, nonce, tag,
signature, and KEM ciphertext). Decryption happens client-side or in the WebSocket
handler when delivering to the recipient.
"""

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
) -> MessageRecord:
    """
    Persist an encrypted message to the database.

    All data is stored in encrypted form — plaintext is NEVER written to disk.

    Args:
        db: SQLAlchemy database session.
        sender: Sender's username.
        receiver: Receiver's username.
        ciphertext_hex: AES-GCM ciphertext (hex-encoded).
        nonce_hex: AES-GCM nonce/IV (hex-encoded).
        tag_hex: AES-GCM authentication tag (hex-encoded).
        signature_hex: ML-DSA-44 signature of the ciphertext (hex-encoded).
        kem_ciphertext_hex: Kyber KEM ciphertext for key decapsulation (hex-encoded).

    Returns:
        The saved MessageRecord.
    """
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
    Retrieve encrypted message history between two users.

    Returns messages in both directions (A→B and B→A), ordered by timestamp.

    Args:
        db: SQLAlchemy database session.
        user_a: First user's username.
        user_b: Second user's username.

    Returns:
        List of message dicts with all encrypted fields.
    """
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
