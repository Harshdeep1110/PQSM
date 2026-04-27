"""
Module: backend.messaging.ws_handler
Purpose: WebSocket handler for real-time encrypted messaging.
         Phase 7: Adds audit logging for all crypto operations.
Created by: TASK-07, Modified by: TASK-30 (audit logging)

Message flow:
  1. Sender sends plaintext via WebSocket
  2. Server encapsulates shared secret with receiver's Kyber public key
  3. Server encrypts plaintext with AES-256-GCM using the shared secret
  4. Server signs the ciphertext with sender's ML-DSA-44 private key
  5. Server forwards encrypted package to receiver
  6. Server sends crypto_trace to BOTH sender and receiver
  7. Receiver decapsulates → verifies signature → decrypts → gets plaintext
  All steps are logged to the audit trail via Cloud Logging.
"""

import json
import logging
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.crypto.kyber import encapsulate, decapsulate
from backend.crypto.aes_gcm import encrypt, decrypt
from backend.crypto.dilithium import sign_message, verify_signature
from backend.auth.user_manager import get_user
from backend.messaging.message_store import save_message
from backend.services.audit_logger import log_crypto_event, CryptoTimer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """Manages active WebSocket connections and session keys."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_keys: dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        logger.info(f"User '{username}' connected. Online: {self.get_online_users()}")

    def disconnect(self, username: str):
        self.active_connections.pop(username, None)
        self.user_keys.pop(username, None)
        logger.info(f"User '{username}' disconnected.")

    def store_keys(self, username: str, kyber_secret: bytes, dilithium_sign: bytes):
        self.user_keys[username] = {
            "kyber_secret": kyber_secret,
            "dilithium_sign": dilithium_sign,
        }

    def get_keys(self, username: str) -> dict | None:
        return self.user_keys.get(username)

    def get_online_users(self) -> list[str]:
        return list(self.active_connections.keys())

    async def send_json(self, username: str, data: dict):
        ws = self.active_connections.get(username)
        if ws:
            await ws.send_json(data)

    async def broadcast_user_list(self):
        users = self.get_online_users()
        for username in users:
            await self.send_json(username, {
                "type": "user_list",
                "users_online": users,
            })


# Global connection manager instance
manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket Message Handler
# ---------------------------------------------------------------------------
async def handle_websocket(websocket: WebSocket, username: str, db: Session):
    """Main WebSocket handler for a connected user."""
    await manager.connect(websocket, username)
    await manager.broadcast_user_list()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "auth":
                await handle_auth(username, data)
            elif msg_type == "chat":
                await handle_chat_message(username, data, db)
            elif msg_type == "ping":
                await manager.send_json(username, {"type": "pong"})
            else:
                await manager.send_json(username, {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_user_list()
    except Exception as e:
        logger.error(f"WebSocket error for '{username}': {e}")
        manager.disconnect(username)
        await manager.broadcast_user_list()


# ---------------------------------------------------------------------------
# Auth Handler
# ---------------------------------------------------------------------------
async def handle_auth(username: str, data: dict):
    """Store user's private keys in memory for the session."""
    try:
        kyber_secret = bytes.fromhex(data["secret_key_kyber_hex"])
        dilithium_sign = bytes.fromhex(data["sign_key_dilithium_hex"])
        manager.store_keys(username, kyber_secret, dilithium_sign)
        await manager.send_json(username, {
            "type": "auth_success",
            "message": f"Keys loaded for session. Welcome, {username}!",
            "users_online": manager.get_online_users(),
        })
    except (KeyError, ValueError) as e:
        await manager.send_json(username, {
            "type": "error",
            "message": f"Auth failed: {e}",
        })


# ---------------------------------------------------------------------------
# Chat Message Handler — Full Encryption Pipeline with Audit Logging
# ---------------------------------------------------------------------------
async def handle_chat_message(sender_name: str, data: dict, db: Session):
    """
    Process a chat message through the PQC encryption pipeline.
    All crypto operations are instrumented with audit logging.
    """
    recipient_name = data.get("to", "")
    plaintext = data.get("plaintext", "")

    if not recipient_name or not plaintext:
        await manager.send_json(sender_name, {
            "type": "error",
            "message": "Missing 'to' or 'plaintext' field.",
        })
        return

    sender_keys = manager.get_keys(sender_name)
    if not sender_keys:
        await manager.send_json(sender_name, {
            "type": "error",
            "message": "Not authenticated. Send 'auth' message with your keys first.",
        })
        return

    receiver = get_user(db, recipient_name)
    if not receiver:
        await manager.send_json(sender_name, {
            "type": "error",
            "message": f"User '{recipient_name}' not found.",
        })
        return

    # ---- ENCRYPTION PIPELINE (with audit logging) ----

    # Step 1: Kyber KEM — encapsulate shared secret
    with CryptoTimer("kem_encapsulation", "Kyber512", sender_name):
        kem_ciphertext, shared_secret = encapsulate(receiver.public_key_kyber)

    # Step 2: AES-256-GCM — encrypt the plaintext
    with CryptoTimer("aes_encrypt", "AES-256-GCM", sender_name):
        encrypted = encrypt(plaintext, shared_secret)

    # Step 3: ML-DSA-44 — sign the ciphertext
    with CryptoTimer("signature_sign", "ML-DSA-44", sender_name):
        ciphertext_bytes = bytes.fromhex(encrypted["ciphertext_hex"])
        signature = sign_message(ciphertext_bytes, sender_keys["dilithium_sign"])

    # Step 4: Save encrypted message to database
    save_message(
        db=db,
        sender=sender_name,
        receiver=recipient_name,
        ciphertext_hex=encrypted["ciphertext_hex"],
        nonce_hex=encrypted["nonce_hex"],
        tag_hex=encrypted["tag_hex"],
        signature_hex=signature.hex(),
        kem_ciphertext_hex=kem_ciphertext.hex(),
    )

    # Step 5: Build crypto trace
    timestamp_str = datetime.now(timezone.utc).isoformat()
    crypto_trace = {
        "type": "crypto_trace",
        "sender": sender_name,
        "receiver": recipient_name,
        "plaintext": plaintext,
        "shared_secret_hex": shared_secret.hex(),
        "kem_ciphertext_hex": kem_ciphertext.hex(),
        "ciphertext_hex": encrypted["ciphertext_hex"],
        "nonce_hex": encrypted["nonce_hex"],
        "tag_hex": encrypted["tag_hex"],
        "signature_hex": signature.hex(),
        "algorithm_kem": "Kyber512",
        "algorithm_sig": "ML-DSA-44",
        "algorithm_sym": "AES-256-GCM",
        "timestamp": timestamp_str,
    }

    # Step 6: Send crypto trace to SENDER
    sender_trace = {**crypto_trace, "direction": "sent"}
    await manager.send_json(sender_name, sender_trace)

    # Step 7: If receiver is online, decrypt and deliver + send trace
    if recipient_name in manager.active_connections:
        receiver_keys = manager.get_keys(recipient_name)

        if receiver_keys:
            try:
                # Receiver-side decryption with audit logging
                with CryptoTimer("kem_decapsulation", "Kyber512", recipient_name):
                    recovered_secret = decapsulate(
                        receiver_keys["kyber_secret"], kem_ciphertext
                    )

                with CryptoTimer("signature_verify", "ML-DSA-44", recipient_name):
                    sender_user = get_user(db, sender_name)
                    sig_valid = verify_signature(
                        ciphertext_bytes, signature, sender_user.public_key_dilithium
                    )

                with CryptoTimer("aes_decrypt", "AES-256-GCM", recipient_name):
                    decrypted_text = decrypt(
                        encrypted["ciphertext_hex"],
                        encrypted["nonce_hex"],
                        encrypted["tag_hex"],
                        recovered_secret,
                    )

                await manager.send_json(recipient_name, {
                    "type": "decrypted_message",
                    "sender": sender_name,
                    "receiver": recipient_name,
                    "plaintext": decrypted_text,
                    "signature_valid": sig_valid,
                    "timestamp": timestamp_str,
                })

                receiver_trace = {**crypto_trace, "direction": "received"}
                await manager.send_json(recipient_name, receiver_trace)

            except Exception as e:
                logger.error(f"Decryption error for {recipient_name}: {e}")
                log_crypto_event("aes_decrypt", "AES-256-GCM", recipient_name, success=False)
                await manager.send_json(recipient_name, {
                    "type": "encrypted_message",
                    "sender": sender_name,
                    "ciphertext_hex": encrypted["ciphertext_hex"],
                    "nonce_hex": encrypted["nonce_hex"],
                    "tag_hex": encrypted["tag_hex"],
                    "signature_hex": signature.hex(),
                    "kem_ciphertext_hex": kem_ciphertext.hex(),
                })
        else:
            await manager.send_json(recipient_name, {
                "type": "encrypted_message",
                "sender": sender_name,
                "ciphertext_hex": encrypted["ciphertext_hex"],
                "nonce_hex": encrypted["nonce_hex"],
                "tag_hex": encrypted["tag_hex"],
                "signature_hex": signature.hex(),
                "kem_ciphertext_hex": kem_ciphertext.hex(),
            })

    # Confirm to sender
    await manager.send_json(sender_name, {
        "type": "message_sent",
        "to": recipient_name,
        "timestamp": timestamp_str,
    })
