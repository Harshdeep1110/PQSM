"""
Module: backend.messaging.ws_handler
Purpose: WebSocket connection handler for real-time encrypted messaging.
         Manages active connections, handles message encryption/decryption flow,
         and sends crypto traces for the Encryption Visualizer.
Created by: TASK-07

Message flow:
  1. Sender sends plaintext via WebSocket
  2. Server encapsulates shared secret with receiver's Kyber public key
  3. Server encrypts plaintext with AES-256-GCM using the shared secret
  4. Server signs the ciphertext with sender's ML-DSA-44 private key
  5. Server forwards encrypted package to receiver
  6. Server sends crypto_trace to BOTH sender and receiver for the visualizer
  7. Receiver decapsulates → verifies signature → decrypts → gets plaintext
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

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """
    Manages active WebSocket connections.
    Maps usernames to their WebSocket instances + session keys.
    """

    def __init__(self):
        # {username: WebSocket}
        self.active_connections: dict[str, WebSocket] = {}
        # {username: {"kyber_secret": bytes, "dilithium_sign": bytes}}
        # Client sends their private keys on connect (kept in memory only)
        self.user_keys: dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, username: str):
        """Accept a WebSocket connection and register the user."""
        await websocket.accept()
        self.active_connections[username] = websocket
        logger.info(f"User '{username}' connected. Online: {self.get_online_users()}")

    def disconnect(self, username: str):
        """Remove a user's connection."""
        self.active_connections.pop(username, None)
        self.user_keys.pop(username, None)
        logger.info(f"User '{username}' disconnected.")

    def store_keys(self, username: str, kyber_secret: bytes, dilithium_sign: bytes):
        """Store user's private keys in memory for the session."""
        self.user_keys[username] = {
            "kyber_secret": kyber_secret,
            "dilithium_sign": dilithium_sign,
        }

    def get_keys(self, username: str) -> dict | None:
        """Get user's session keys."""
        return self.user_keys.get(username)

    def get_online_users(self) -> list[str]:
        """Get list of currently connected usernames."""
        return list(self.active_connections.keys())

    async def send_json(self, username: str, data: dict):
        """Send JSON data to a specific user."""
        ws = self.active_connections.get(username)
        if ws:
            await ws.send_json(data)

    async def broadcast_user_list(self):
        """Broadcast the updated online user list to all connected clients."""
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
    """
    Main WebSocket handler for a connected user.

    Protocol:
    1. Client connects → sends 'auth' message with private keys
    2. Client sends 'chat' messages with {to, plaintext}
    3. Server handles all encryption and forwards to recipient
    """
    await manager.connect(websocket, username)
    await manager.broadcast_user_list()

    try:
        while True:
            # Receive message from client
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "auth":
                # Client sends their private keys for this session
                await handle_auth(username, data)

            elif msg_type == "chat":
                # Client sends a plaintext message to encrypt and forward
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
    """
    Store the user's private keys in memory for encryption/signing.
    These keys are only held in RAM for the session duration.
    """
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
# Chat Message Handler — Full Encryption Pipeline
# ---------------------------------------------------------------------------
async def handle_chat_message(sender_name: str, data: dict, db: Session):
    """
    Process a chat message through the full PQC encryption pipeline:
    1. Kyber KEM → shared secret
    2. AES-256-GCM encrypt with shared secret
    3. ML-DSA-44 sign the ciphertext
    4. Forward to receiver + send crypto traces to both parties
    """
    recipient_name = data.get("to", "")
    plaintext = data.get("plaintext", "")

    if not recipient_name or not plaintext:
        await manager.send_json(sender_name, {
            "type": "error",
            "message": "Missing 'to' or 'plaintext' field.",
        })
        return

    # Get sender's signing key from session
    sender_keys = manager.get_keys(sender_name)
    if not sender_keys:
        await manager.send_json(sender_name, {
            "type": "error",
            "message": "Not authenticated. Send 'auth' message with your keys first.",
        })
        return

    # Look up receiver's public keys from the database
    receiver = get_user(db, recipient_name)
    if not receiver:
        await manager.send_json(sender_name, {
            "type": "error",
            "message": f"User '{recipient_name}' not found.",
        })
        return

    # ---- ENCRYPTION PIPELINE ----

    # Step 1: Kyber KEM — encapsulate a shared secret with receiver's public key
    kem_ciphertext, shared_secret = encapsulate(receiver.public_key_kyber)

    # Step 2: AES-256-GCM — encrypt the plaintext with the shared secret
    encrypted = encrypt(plaintext, shared_secret)

    # Step 3: ML-DSA-44 — sign the ciphertext with sender's private key
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

    # Step 5: Build crypto trace for the Encryption Visualizer
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

    # Step 6: Send crypto trace to SENDER (direction: "sent")
    sender_trace = {**crypto_trace, "direction": "sent"}
    await manager.send_json(sender_name, sender_trace)

    # Step 7: If receiver is online, decrypt and deliver + send trace
    if recipient_name in manager.active_connections:
        receiver_keys = manager.get_keys(recipient_name)

        if receiver_keys:
            try:
                #  Receiver-side decryption pipeline:
                # 7a. Kyber decapsulate → recover shared secret
                recovered_secret = decapsulate(
                    receiver_keys["kyber_secret"], kem_ciphertext
                )

                # 7b. Verify sender's signature
                sender_user = get_user(db, sender_name)
                sig_valid = verify_signature(
                    ciphertext_bytes, signature, sender_user.public_key_dilithium
                )

                # 7c. AES-GCM decrypt
                decrypted_text = decrypt(
                    encrypted["ciphertext_hex"],
                    encrypted["nonce_hex"],
                    encrypted["tag_hex"],
                    recovered_secret,
                )

                # Send decrypted message to receiver
                await manager.send_json(recipient_name, {
                    "type": "decrypted_message",
                    "sender": sender_name,
                    "receiver": recipient_name,
                    "plaintext": decrypted_text,
                    "signature_valid": sig_valid,
                    "timestamp": timestamp_str,
                })

                # Send crypto trace to receiver (direction: "received")
                receiver_trace = {**crypto_trace, "direction": "received"}
                await manager.send_json(recipient_name, receiver_trace)

            except Exception as e:
                logger.error(f"Decryption error for {recipient_name}: {e}")
                # Forward the encrypted package so client can try decrypting
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
            # Receiver connected but not authenticated — send encrypted
            await manager.send_json(recipient_name, {
                "type": "encrypted_message",
                "sender": sender_name,
                "ciphertext_hex": encrypted["ciphertext_hex"],
                "nonce_hex": encrypted["nonce_hex"],
                "tag_hex": encrypted["tag_hex"],
                "signature_hex": signature.hex(),
                "kem_ciphertext_hex": kem_ciphertext.hex(),
            })

    # Confirm to sender that the message was sent
    await manager.send_json(sender_name, {
        "type": "message_sent",
        "to": recipient_name,
        "timestamp": timestamp_str,
    })
