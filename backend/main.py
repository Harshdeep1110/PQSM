"""
Module: backend.main
Purpose: FastAPI application entry point.
         Defines REST API endpoints and WebSocket endpoint for the PQC Messenger.
Created by: TASK-08

Endpoints:
  POST /register          — Register a new user (returns private keys one-time)
  GET  /users             — List all registered users
  GET  /messages/{a}/{b}  — Fetch encrypted message history between two users
  WS   /ws/{username}     — WebSocket for real-time encrypted messaging

Run with: uvicorn backend.main:app --reload
"""

import os

from dotenv import load_dotenv

# Load .env file if present (for local development)
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, WebSocket, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, SessionLocal
from backend.auth.user_manager import register_user, list_users, get_user, verify_user_keys
from backend.messaging.message_store import get_messages
from backend.messaging.ws_handler import handle_websocket, manager
from backend.media.file_handler import encrypt_and_store_file, decrypt_file, ALLOWED_MIME_TYPES
from backend.media.file_store import save_media_record, get_media_record, get_media_history
from backend.models import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    UserListResponse,
    UserInfo,
    MessageHistoryResponse,
    MessageInfo,
    MediaUploadResponse,
    MediaFileInfo,
    MediaHistoryResponse,
)

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PQC Messenger",
    description="Post-Quantum Secure Messaging System using Kyber512 + ML-DSA-44 + AES-256-GCM",
    version="2.0.0",
)

# CORS — reads allowed origins from env var, falls back to wildcard for local dev
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins_str == "*":
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---------------------------------------------------------------------------
# Startup Event
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """Initialize the database tables on server start."""
    init_db()


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "service": "PQC Messenger",
        "status": "running",
        "algorithms": {
            "kem": "Kyber512",
            "signature": "ML-DSA-44 (Dilithium2)",
            "symmetric": "AES-256-GCM",
        },
    }


@app.post("/register", response_model=RegisterResponse, tags=["Users"])
def api_register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    Generates Kyber512 (KEM) and ML-DSA-44 (signature) keypairs.
    Returns private keys ONE TIME ONLY — the client must store them securely.
    Public keys are stored on the server for other users to encrypt/verify.
    """
    try:
        result = register_user(db, request.username, request.password)
        return RegisterResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login", response_model=LoginResponse, tags=["Users"])
def api_login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a returning user.

    Verifies that the provided private keys match the stored public keys
    by performing a Kyber KEM round-trip test.
    """
    try:
        result = verify_user_keys(
            db,
            request.username,
            request.password,
            request.secret_key_kyber_hex,
            request.sign_key_dilithium_hex,
        )
        return LoginResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/users", response_model=UserListResponse, tags=["Users"])
def api_list_users(db: Session = Depends(get_db)):
    """List all registered users with their public keys."""
    users = list_users(db)
    return UserListResponse(
        users=[UserInfo(**u) for u in users],
        count=len(users),
    )


@app.get("/messages/{user_a}/{user_b}", response_model=MessageHistoryResponse, tags=["Messages"])
def api_get_messages(user_a: str, user_b: str, db: Session = Depends(get_db)):
    """
    Fetch encrypted message history between two users.
    Messages are returned in encrypted form — decryption is client-side.
    """
    messages = get_messages(db, user_a, user_b)
    return MessageHistoryResponse(
        messages=[MessageInfo(**m) for m in messages],
        count=len(messages),
    )


# ---------------------------------------------------------------------------
# Media Endpoints (TASK-18)
# ---------------------------------------------------------------------------
@app.post("/upload", response_model=MediaUploadResponse, tags=["Media"])
async def api_upload_file(
    file: UploadFile = File(...),
    sender: str = Form(...),
    receiver: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload and encrypt a media file.

    The file is encrypted with a FRESH Kyber KEM operation (one-time use),
    AES-256-GCM for symmetric encryption, and signed with the sender's
    Dilithium key. Only the encrypted bytes are stored on disk.
    """
    # Validate content type — strip parameters (e.g. "video/mp4; codecs=avc1" → "video/mp4")
    clean_content_type = file.content_type.split(';')[0].strip().lower() if file.content_type else None
    if clean_content_type and clean_content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    # Read file bytes
    file_bytes = await file.read()

    # Look up sender and receiver
    sender_user = get_user(db, sender)
    if not sender_user:
        raise HTTPException(status_code=404, detail=f"Sender '{sender}' not found.")

    receiver_user = get_user(db, receiver)
    if not receiver_user:
        raise HTTPException(status_code=404, detail=f"Receiver '{receiver}' not found.")

    # Get sender's signing key from the WebSocket session
    sender_keys = manager.get_keys(sender)
    if not sender_keys:
        raise HTTPException(
            status_code=401,
            detail="Sender not authenticated via WebSocket. Connect and send auth message first.",
        )

    try:
        # Encrypt and store the file
        result = encrypt_and_store_file(
            file_bytes=file_bytes,
            filename=file.filename or "unnamed",
            content_type=file.content_type,
            sender=sender,
            receiver_public_key=receiver_user.public_key_kyber,
            sender_sign_key=sender_keys["dilithium_sign"],
        )

        # Save metadata to database
        media_id = save_media_record(
            db=db,
            sender=sender,
            receiver=receiver,
            file_type=result["file_type"],
            original_filename=result["original_filename"],
            stored_filename=result["stored_filename"],
            encrypted_path=result["encrypted_path"],
            file_size_bytes=result["file_size_bytes"],
            nonce_hex=result["nonce_hex"],
            tag_hex=result["tag_hex"],
            kem_ciphertext_hex=result["kem_ciphertext_hex"],
            signature_hex=result["signature_hex"],
        )

        # Push WebSocket notification to receiver if online
        if receiver in manager.active_connections:
            await manager.send_json(receiver, {
                "type": "media_message",
                "media_id": media_id,
                "sender": sender,
                "receiver": receiver,
                "file_type": result["file_type"],
                "original_filename": result["original_filename"],
                "file_size_bytes": result["file_size_bytes"],
            })

        # Also send media crypto trace to sender for the visualizer
        await manager.send_json(sender, {
            "type": "media_crypto_trace",
            "direction": "sent",
            "media_id": media_id,
            "sender": sender,
            "receiver": receiver,
            "file_type": result["file_type"],
            "original_filename": result["original_filename"],
            "file_size_bytes": result["file_size_bytes"],
            "kem_ciphertext_hex": result["kem_ciphertext_hex"],
            "nonce_hex": result["nonce_hex"],
            "tag_hex": result["tag_hex"],
            "signature_hex": result["signature_hex"],
            "algorithm_kem": "Kyber512",
            "algorithm_sig": "ML-DSA-44",
            "algorithm_sym": "AES-256-GCM",
        })

        # Fetch the saved record for timestamp
        record = get_media_record(db, media_id)

        return MediaUploadResponse(
            media_id=media_id,
            file_type=result["file_type"],
            original_filename=result["original_filename"],
            file_size_bytes=result["file_size_bytes"],
            timestamp=record.timestamp if record else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/media/{media_id}", tags=["Media"])
def api_get_media(
    media_id: str,
    receiver_username: str,
    db: Session = Depends(get_db),
):
    """
    Download/stream a decrypted media file.

    The receiver's Kyber secret key (from their active WebSocket session) is used
    to decapsulate the per-file shared secret and decrypt the file in memory.
    Decrypted bytes are streamed — never written to a temp file.
    """
    record = get_media_record(db, media_id)
    if not record:
        raise HTTPException(status_code=404, detail="Media file not found.")

    # Verify the requester is the intended receiver (or sender)
    if receiver_username != record.receiver and receiver_username != record.sender:
        raise HTTPException(status_code=403, detail="You are not authorized to access this file.")

    # Get receiver's Kyber secret key from active WebSocket session
    # For the sender viewing their own upload, we need the receiver's key to decrypt
    # So we use the actual receiver's key
    decrypt_user = record.receiver
    user_keys = manager.get_keys(decrypt_user)
    if not user_keys:
        raise HTTPException(
            status_code=401,
            detail=f"Receiver '{decrypt_user}' is not online. The file can only be decrypted when the receiver has an active session.",
        )

    try:
        decrypted_bytes = decrypt_file(
            stored_filename=record.stored_filename,
            kem_ciphertext_hex=record.kem_ciphertext_hex,
            nonce_hex=record.nonce_hex,
            tag_hex=record.tag_hex,
            receiver_secret_key=user_keys["kyber_secret"],
        )

        # Determine content type from file_type
        ext = os.path.splitext(record.original_filename)[1].lower()
        content_type_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".webp": "image/webp",
            ".mp4": "video/mp4", ".webm": "video/webm",
            ".mov": "video/quicktime", ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska", ".3gp": "video/3gpp",
            ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav",
            # Documents
            ".pdf": "application/pdf", ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".zip": "application/zip", ".txt": "text/plain", ".csv": "text/csv",
        }
        ct = content_type_map.get(ext, "application/octet-stream")

        # Build Content-Disposition with Unicode-safe filename
        # ASCII fallback for basic 'filename', RFC 5987 'filename*' for Unicode
        from urllib.parse import quote
        ascii_name = record.original_filename.encode('ascii', 'replace').decode('ascii')
        utf8_name = quote(record.original_filename)

        return Response(
            content=decrypted_bytes,
            media_type=ct,
            headers={
                "Content-Disposition": f"inline; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}",
            },
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Encrypted file not found on disk.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {e}")


@app.get("/media/history/{user_a}/{user_b}", response_model=MediaHistoryResponse, tags=["Media"])
def api_get_media_history(
    user_a: str,
    user_b: str,
    db: Session = Depends(get_db),
):
    """Fetch media file history between two users."""
    media = get_media_history(db, user_a, user_b)
    return MediaHistoryResponse(
        media=[MediaFileInfo(**m) for m in media],
        count=len(media),
    )


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """
    WebSocket endpoint for real-time encrypted messaging.

    Protocol:
    1. Connect to /ws/{username}
    2. Send auth message: {"type": "auth", "secret_key_kyber_hex": "...", "sign_key_dilithium_hex": "..."}
    3. Send chat messages: {"type": "chat", "to": "recipient", "plaintext": "Hello!"}
    4. Receive: decrypted_message, crypto_trace, user_list, message_sent, errors
    """
    # Create a dedicated DB session for this WebSocket connection
    db = SessionLocal()
    try:
        await handle_websocket(websocket, username, db)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
