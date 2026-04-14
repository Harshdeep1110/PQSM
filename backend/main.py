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

from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, SessionLocal
from backend.auth.user_manager import register_user, list_users, get_user, verify_user_keys
from backend.messaging.message_store import get_messages
from backend.messaging.ws_handler import handle_websocket
from backend.models import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    UserListResponse,
    UserInfo,
    MessageHistoryResponse,
    MessageInfo,
)

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PQC Messenger",
    description="Post-Quantum Secure Messaging System using Kyber512 + ML-DSA-44 + AES-256-GCM",
    version="1.0.0",
)

# CORS middleware for local development (React frontend on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
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
