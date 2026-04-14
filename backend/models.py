"""
Module: backend.models
Purpose: Pydantic data models for API request/response bodies.
         Defines the shape of all data flowing through REST and WebSocket endpoints.
Created by: TASK-05 / TASK-08

These models provide validation, serialization, and documentation for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# User Models
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    """Request body for POST /register"""
    username: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique username for the new user",
    )
    password: str = Field(
        ...,
        min_length=4,
        max_length=128,
        description="Password for account authentication",
    )


class RegisterResponse(BaseModel):
    """
    Response from POST /register.
    Returns the user's private keys (ONE TIME ONLY — client must store them).
    Public keys are stored server-side.
    """
    username: str
    # Private keys returned as hex strings for easy client-side storage
    secret_key_kyber_hex: str
    sign_key_dilithium_hex: str
    # Public keys also returned so the client knows their own identity
    public_key_kyber_hex: str
    verify_key_dilithium_hex: str
    message: str = "Registration successful. Store your private keys securely!"


class LoginRequest(BaseModel):
    """Request body for POST /login — returning user authentication."""
    username: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Username of the returning user",
    )
    password: str = Field(
        ...,
        min_length=4,
        max_length=128,
        description="Account password",
    )
    secret_key_kyber_hex: str = Field(
        ..., description="User's Kyber512 private key (hex-encoded)"
    )
    sign_key_dilithium_hex: str = Field(
        ..., description="User's ML-DSA-44 signing key (hex-encoded)"
    )


class LoginResponse(BaseModel):
    """
    Response from POST /login.
    Confirms the user's private keys match their stored public keys.
    """
    username: str
    public_key_kyber_hex: str
    verify_key_dilithium_hex: str
    message: str = "Login successful. Welcome back!"


class UserInfo(BaseModel):
    """Public user info returned by GET /users"""
    username: str
    public_key_kyber_hex: str
    verify_key_dilithium_hex: str
    created_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Response from GET /users"""
    users: list[UserInfo]
    count: int


# ---------------------------------------------------------------------------
# Message Models
# ---------------------------------------------------------------------------
class MessageInfo(BaseModel):
    """A single encrypted message record"""
    id: int
    sender: str
    receiver: str
    ciphertext_hex: str
    nonce_hex: str
    tag_hex: str
    signature_hex: str
    kem_ciphertext_hex: str
    timestamp: Optional[datetime] = None


class MessageHistoryResponse(BaseModel):
    """Response from GET /messages/{user_a}/{user_b}"""
    messages: list[MessageInfo]
    count: int


# ---------------------------------------------------------------------------
# WebSocket Message Models
# ---------------------------------------------------------------------------
class WSMessage(BaseModel):
    """
    Message sent over WebSocket from client to server.
    The client sends plaintext; the server handles all encryption.
    """
    type: str = Field(
        default="chat",
        description="Message type: 'chat' for regular messages",
    )
    to: str = Field(..., description="Recipient username")
    plaintext: str = Field(..., description="Message text to encrypt and send")


class WSEncryptedPackage(BaseModel):
    """
    Encrypted message package forwarded to the receiver via WebSocket.
    Contains everything needed to decrypt + verify.
    """
    type: str = "encrypted_message"
    sender: str
    ciphertext_hex: str
    nonce_hex: str
    tag_hex: str
    signature_hex: str
    kem_ciphertext_hex: str  # Receiver needs this to decapsulate shared secret


class WSCryptoTrace(BaseModel):
    """
    Detailed crypto trace sent back to BOTH sender and receiver
    for the Encryption Visualizer UI component.
    """
    type: str = "crypto_trace"
    direction: str  # "sent" or "received"
    sender: str
    receiver: str
    plaintext: str
    shared_secret_hex: str
    kem_ciphertext_hex: str
    ciphertext_hex: str
    nonce_hex: str
    tag_hex: str
    signature_hex: str
    algorithm_kem: str = "Kyber512"
    algorithm_sig: str = "ML-DSA-44"
    algorithm_sym: str = "AES-256-GCM"


class WSDeliveredMessage(BaseModel):
    """
    Decrypted message delivered to the receiver's UI.
    """
    type: str = "decrypted_message"
    sender: str
    plaintext: str
    timestamp: Optional[str] = None


class WSStatusMessage(BaseModel):
    """Status/error messages sent to clients."""
    type: str = "status"
    message: str
    users_online: Optional[list[str]] = None
