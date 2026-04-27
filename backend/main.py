"""
Module: backend.main
Purpose: FastAPI application entry point.
         Defines REST API endpoints and WebSocket endpoint for the PQC Messenger.
         Phase 7: Adds Firebase Authentication, Firestore, GCS, KMS, and Audit Logging.
Created by: TASK-08, Modified by: TASK-26/27/28/30/31

Endpoints:
  POST /register          — Register (local auth mode)
  POST /login             — Login (local auth mode)
  POST /auth/register     — Register via Firebase
  POST /auth/login        — Login via Firebase
  GET  /users             — List all registered users
  GET  /messages/{a}/{b}  — Fetch message history
  GET  /audit/logs        — Fetch crypto audit log entries
  POST /upload            — Upload encrypted media file
  GET  /media/{id}        — Download/stream decrypted media
  GET  /media/history/{a}/{b} — Media history
  WS   /ws/{username}     — WebSocket for real-time encrypted messaging
"""

import os

from dotenv import load_dotenv

# Load .env file if present (for local development)
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, WebSocket, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, SessionLocal
from backend.auth.user_manager import register_user, list_users, get_user, verify_user_keys
from backend.messaging.message_store import get_messages
from backend.messaging.ws_handler import handle_websocket, manager
from backend.media.file_handler import encrypt_and_store_file, decrypt_file, ALLOWED_MIME_TYPES
from backend.media.file_store import save_media_record, get_media_record, get_media_history
from backend.services.firebase_auth import USE_FIREBASE_AUTH, verify_firebase_token
from backend.services.firestore_service import (
    is_firestore_enabled, save_user_firestore, get_user_by_username_firestore,
    list_users_firestore,
)
from backend.services.audit_logger import get_recent_logs, log_crypto_event
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
    FirebaseRegisterRequest,
    FirebaseLoginRequest,
    AuditLogEntry,
    AuditLogResponse,
)

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PQC Messenger",
    description="Post-Quantum Secure Messaging System using Kyber512 + ML-DSA-44 + AES-256-GCM. "
                "Deployed on Google Cloud with Firebase Auth, Firestore, GCS, KMS, and Cloud Logging.",
    version="3.0.0",
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
# Global Exception Handler (Fixes CORS missing on 500 errors)
# ---------------------------------------------------------------------------
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logger.error(f"Global Exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
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
        "version": "3.0.0",
        "algorithms": {
            "kem": "Kyber512",
            "signature": "ML-DSA-44 (Dilithium2)",
            "symmetric": "AES-256-GCM",
        },
        "google_integrations": {
            "firebase_auth": USE_FIREBASE_AUTH,
            "firestore": is_firestore_enabled(),
            "cloud_storage": is_firestore_enabled(),
            "cloud_kms": os.environ.get("ENABLE_KMS", "false").lower() == "true",
            "cloud_logging": os.environ.get("ENABLE_AUDIT_LOGGING", "false").lower() == "true",
        },
    }


# ---------------------------------------------------------------------------
# Local Auth Endpoints (backward compatible)
# ---------------------------------------------------------------------------
@app.post("/register", response_model=RegisterResponse, tags=["Auth (Local)"])
def api_register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (local auth mode)."""
    try:
        result = register_user(db, request.username, request.password)
        return RegisterResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login", response_model=LoginResponse, tags=["Auth (Local)"])
def api_login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a returning user (local auth mode)."""
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


# ---------------------------------------------------------------------------
# Firebase Auth Endpoints (Phase 7 — TASK-26)
# ---------------------------------------------------------------------------
@app.post("/auth/register", response_model=RegisterResponse, tags=["Auth (Firebase)"])
def api_firebase_register(
    request: FirebaseRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user via Firebase Authentication.

    1. Verify the Firebase ID token
    2. Generate Kyber512 + ML-DSA-44 keypairs
    3. Store public keys in Firestore (or SQLite in local mode)
    4. Return private keys ONE TIME ONLY
    """
    # Verify Firebase token
    try:
        firebase_user = verify_firebase_token(request.firebase_id_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    username = request.username

    # Generate PQC keypairs
    from backend.crypto.kyber import generate_keypair as kyber_generate_keypair
    from backend.crypto.dilithium import generate_signing_keypair

    kyber_public, kyber_secret = kyber_generate_keypair()
    dilithium_verify, dilithium_sign = generate_signing_keypair()

    # Log key generation event
    log_crypto_event("key_generation", "Kyber512", firebase_user["uid"])
    log_crypto_event("key_generation", "ML-DSA-44", firebase_user["uid"])

    if is_firestore_enabled():
        # Check if user already exists in Firestore
        existing = get_user_by_username_firestore(username)
        if existing:
            raise HTTPException(status_code=400, detail=f"Username '{username}' is already registered.")

        # Save to Firestore
        save_user_firestore(
            uid=firebase_user["uid"],
            username=username,
            email=firebase_user["email"],
            public_key_kyber_hex=kyber_public.hex(),
            public_key_dilithium_hex=dilithium_verify.hex(),
        )
    else:
        # Fallback: save to SQLite
        try:
            register_user(db, username, "firebase-managed")
        except ValueError:
            pass  # User might already exist in SQLite

    return RegisterResponse(
        username=username,
        secret_key_kyber_hex=kyber_secret.hex(),
        sign_key_dilithium_hex=dilithium_sign.hex(),
        public_key_kyber_hex=kyber_public.hex(),
        verify_key_dilithium_hex=dilithium_verify.hex(),
        message="Registration successful via Firebase. Store your private keys securely!",
    )


@app.post("/auth/login", response_model=LoginResponse, tags=["Auth (Firebase)"])
def api_firebase_login(
    request: FirebaseLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login via Firebase Authentication.

    1. Verify the Firebase ID token
    2. Verify that the provided PQC keys match stored public keys
    3. Return confirmation
    """
    try:
        firebase_user = verify_firebase_token(request.firebase_id_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if is_firestore_enabled():
        from backend.services.firestore_service import get_user_firestore
        user_data = get_user_firestore(firebase_user["uid"])
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found. Please register first.")

        # Verify Kyber key via KEM round-trip
        from backend.crypto.kyber import encapsulate, decapsulate
        try:
            pub_key = bytes.fromhex(user_data["public_key_kyber_hex"])
            sec_key = bytes.fromhex(request.secret_key_kyber_hex)
            ct, ss = encapsulate(pub_key)
            recovered = decapsulate(sec_key, ct)
            if ss != recovered:
                raise ValueError("Key mismatch")
        except Exception:
            raise HTTPException(status_code=401, detail="PQC key verification failed.")

        return LoginResponse(
            username=user_data["username"],
            public_key_kyber_hex=user_data["public_key_kyber_hex"],
            verify_key_dilithium_hex=user_data["public_key_dilithium_hex"],
            message="Login successful via Firebase. Welcome back!",
        )
    else:
        # Fallback to local auth
        try:
            result = verify_user_keys(
                db, firebase_user.get("name", ""), "firebase-managed",
                request.secret_key_kyber_hex, request.sign_key_dilithium_hex,
            )
            return LoginResponse(**result)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))


# ---------------------------------------------------------------------------
# User Listing (supports Firestore + SQLite)
# ---------------------------------------------------------------------------
@app.get("/users", response_model=UserListResponse, tags=["Users"])
def api_list_users(db: Session = Depends(get_db)):
    """List all registered users with their public keys."""
    if is_firestore_enabled():
        users = list_users_firestore()
    else:
        users = list_users(db)
    return UserListResponse(
        users=[UserInfo(**u) for u in users],
        count=len(users),
    )


@app.get("/messages/{user_a}/{user_b}", response_model=MessageHistoryResponse, tags=["Messages"])
def api_get_messages(user_a: str, user_b: str, db: Session = Depends(get_db)):
    """Fetch encrypted message history between two users."""
    if is_firestore_enabled():
        from backend.services.firestore_service import get_messages_firestore
        messages = get_messages_firestore(user_a, user_b)
    else:
        messages = get_messages(db, user_a, user_b)
    return MessageHistoryResponse(
        messages=[MessageInfo(**m) for m in messages],
        count=len(messages),
    )


# ---------------------------------------------------------------------------
# Audit Log Endpoint (Phase 7 — TASK-30)
# ---------------------------------------------------------------------------
@app.get("/audit/logs", response_model=AuditLogResponse, tags=["Audit"])
def api_get_audit_logs(limit: int = 50):
    """
    Fetch recent cryptographic audit log entries.
    Returns structured log entries from Cloud Logging / in-memory cache.
    Used by the Encryption Visualizer's Audit Log panel.
    """
    logs = get_recent_logs(limit=min(limit, 200))
    return AuditLogResponse(
        logs=[AuditLogEntry(**log) for log in logs],
        count=len(logs),
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
    """Upload and encrypt a media file."""
    try:
        # Validate content type
        clean_content_type = file.content_type.split(';')[0].strip().lower() if file.content_type else None
        if clean_content_type and clean_content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
            )

        file_bytes = await file.read()

        # Look up sender and receiver
        sender_user = get_user(db, sender)
        if not sender_user:
            raise HTTPException(status_code=404, detail=f"Sender '{sender}' not found.")

        receiver_user = get_user(db, receiver)
        if not receiver_user:
            raise HTTPException(status_code=404, detail=f"Receiver '{receiver}' not found.")

        sender_keys = manager.get_keys(sender)
        if not sender_keys:
            raise HTTPException(
                status_code=401,
                detail="Sender not authenticated via WebSocket. Connect and send auth message first.",
            )

        result = encrypt_and_store_file(
            file_bytes=file_bytes,
            filename=file.filename or "unnamed",
            content_type=file.content_type,
            sender=sender,
            receiver_public_key=receiver_user.public_key_kyber,
            sender_sign_key=sender_keys["dilithium_sign"],
        )

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

        record = get_media_record(db, media_id)

        return MediaUploadResponse(
            media_id=media_id,
            file_type=result["file_type"],
            original_filename=result["original_filename"],
            file_size_bytes=result["file_size_bytes"],
            timestamp=record.timestamp if record else None,
        )

    except ValueError as e:
        logger.error(f"Upload ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Upload Exception: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Server error during upload: {str(e)}")


@app.get("/media/{media_id}", tags=["Media"])
def api_get_media(
    media_id: str,
    receiver_username: str,
    db: Session = Depends(get_db),
):
    """Download/stream a decrypted media file."""
    record = get_media_record(db, media_id)
    if not record:
        raise HTTPException(status_code=404, detail="Media file not found.")

    if receiver_username != record.receiver and receiver_username != record.sender:
        raise HTTPException(status_code=403, detail="You are not authorized to access this file.")

    decrypt_user = record.receiver
    user_keys = manager.get_keys(decrypt_user)
    if not user_keys:
        raise HTTPException(
            status_code=401,
            detail=f"Receiver '{decrypt_user}' is not online. File can only be decrypted when receiver has an active session.",
        )

    try:
        decrypted_bytes = decrypt_file(
            stored_filename=record.stored_filename,
            kem_ciphertext_hex=record.kem_ciphertext_hex,
            nonce_hex=record.nonce_hex,
            tag_hex=record.tag_hex,
            receiver_secret_key=user_keys["kyber_secret"],
        )

        ext = os.path.splitext(record.original_filename)[1].lower()
        content_type_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".webp": "image/webp",
            ".mp4": "video/mp4", ".webm": "video/webm",
            ".mov": "video/quicktime", ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska", ".3gp": "video/3gpp",
            ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav",
            ".pdf": "application/pdf", ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".zip": "application/zip", ".txt": "text/plain", ".csv": "text/csv",
        }
        ct = content_type_map.get(ext, "application/octet-stream")

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
    """WebSocket endpoint for real-time encrypted messaging."""
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
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
