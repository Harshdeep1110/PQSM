"""
Module: backend.media.file_handler
Purpose: Encrypt, store, and decrypt media files using the PQC pipeline.
         Each file gets its own fresh Kyber KEM operation — the chat session's
         shared secret is NEVER reused for file encryption.
Created by: TASK-16

Security rules:
  - Filenames sanitized (no path traversal)
  - Max file size: 50MB (configurable via MAX_FILE_SIZE_MB env var)
  - MIME type allowlist enforced
  - Encrypted bytes only on disk — plaintext never written
"""

import os
import uuid
import hashlib
from pathlib import Path

from backend.crypto.kyber import encapsulate, decapsulate
from backend.crypto.aes_gcm import derive_aes_key
from backend.crypto.dilithium import sign_message, verify_signature

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UPLOAD_DIR = os.environ.get(
    "UPLOAD_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"),
)

MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/3gpp",
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/webm",       # Browser-recorded voice messages
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-zip-compressed",
    "text/plain",
    "text/csv",
}

# Map MIME types to file_type categories
MIME_TO_FILE_TYPE = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/webp": "image",
    "video/mp4": "video",
    "video/webm": "video",
    "video/quicktime": "video",
    "video/x-msvideo": "video",
    "video/x-matroska": "video",
    "video/3gpp": "video",
    "audio/mpeg": "audio",
    "audio/ogg": "audio",
    "audio/wav": "audio",
    "audio/webm": "audio",
    # Documents
    "application/pdf": "document",
    "application/msword": "document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
    "application/vnd.ms-excel": "document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "document",
    "application/vnd.ms-powerpoint": "document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "document",
    "application/zip": "document",
    "application/x-zip-compressed": "document",
    "text/plain": "document",
    "text/csv": "document",
}


# ---------------------------------------------------------------------------
# Filename Sanitization
# ---------------------------------------------------------------------------
def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.
    Strips directory separators and rejects '..' sequences.
    """
    # Remove any directory components
    filename = os.path.basename(filename)
    # Reject path traversal attempts
    if ".." in filename:
        raise ValueError("Invalid filename: path traversal detected.")
    # Remove null bytes
    filename = filename.replace("\x00", "")
    if not filename:
        raise ValueError("Invalid filename: empty after sanitization.")
    return filename


# ---------------------------------------------------------------------------
# File Type Detection
# ---------------------------------------------------------------------------
def detect_file_type(content_type: str | None, filename: str) -> str:
    """
    Determine the file type category from the MIME type.
    Falls back to extension-based detection if content_type is missing.
    """
    # Strip MIME parameters before lookup
    clean_type = content_type.split(';')[0].strip().lower() if content_type else None
    if clean_type and clean_type in MIME_TO_FILE_TYPE:
        return MIME_TO_FILE_TYPE[clean_type]

    # Fallback: extension-based detection
    ext = os.path.splitext(filename)[1].lower()
    ext_map = {
        ".jpg": "image", ".jpeg": "image", ".png": "image",
        ".gif": "image", ".webp": "image",
        ".mp4": "video", ".webm": "video", ".mov": "video",
        ".avi": "video", ".mkv": "video", ".3gp": "video",
        ".mp3": "audio", ".ogg": "audio", ".wav": "audio",
        # Documents
        ".pdf": "document", ".doc": "document", ".docx": "document",
        ".xls": "document", ".xlsx": "document",
        ".ppt": "document", ".pptx": "document",
        ".zip": "document", ".txt": "document", ".csv": "document",
    }
    if ext in ext_map:
        return ext_map[ext]

    raise ValueError(f"Unsupported file type: {content_type or ext}")


# ---------------------------------------------------------------------------
# Encrypt & Store File
# ---------------------------------------------------------------------------
def encrypt_and_store_file(
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
    sender: str,
    receiver_public_key: bytes,
    sender_sign_key: bytes,
) -> dict:
    """
    Encrypt a file and store the encrypted bytes to disk.

    Steps:
    1. Validate file size and MIME type
    2. Sanitize filename
    3. Generate a FRESH Kyber KEM pair for this file (one-time use)
    4. Encapsulate shared secret using receiver's Kyber public key
    5. Encrypt file bytes with AES-256-GCM using the shared secret
    6. Sign the encrypted bytes with sender's Dilithium key
    7. Save encrypted bytes to backend/uploads/{uuid}.enc

    Returns:
        dict with: stored_filename, nonce_hex, tag_hex, kem_ciphertext_hex,
                   signature_hex, file_size_bytes, file_type, original_filename
    """
    # --- Validation ---
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.")

    # Strip MIME parameters (e.g. "video/mp4; codecs=avc1" → "video/mp4")
    clean_type = content_type.split(';')[0].strip().lower() if content_type else None

    if clean_type and clean_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {content_type}")

    original_filename = sanitize_filename(filename)
    file_type = detect_file_type(clean_type, original_filename)
    file_size = len(file_bytes)

    # --- Encryption Pipeline ---

    # Step 1: Fresh Kyber KEM — encapsulate shared secret with receiver's public key
    kem_ciphertext, shared_secret = encapsulate(receiver_public_key)

    # Step 2: Derive AES key and encrypt file bytes
    aes_key = derive_aes_key(shared_secret)
    nonce = get_random_bytes(12)
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    encrypted_bytes, tag = cipher.encrypt_and_digest(file_bytes)

    # Step 3: Sign the encrypted bytes with sender's Dilithium key
    signature = sign_message(encrypted_bytes, sender_sign_key)

    # Step 4: Save to disk
    stored_filename = f"{uuid.uuid4()}.enc"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    encrypted_path = os.path.join(UPLOAD_DIR, stored_filename)
    with open(encrypted_path, "wb") as f:
        f.write(encrypted_bytes)

    return {
        "stored_filename": stored_filename,
        "original_filename": original_filename,
        "file_type": file_type,
        "file_size_bytes": file_size,
        "nonce_hex": nonce.hex(),
        "tag_hex": tag.hex(),
        "kem_ciphertext_hex": kem_ciphertext.hex(),
        "signature_hex": signature.hex(),
        "encrypted_path": f"uploads/{stored_filename}",
    }


# ---------------------------------------------------------------------------
# Decrypt File
# ---------------------------------------------------------------------------
def decrypt_file(
    stored_filename: str,
    kem_ciphertext_hex: str,
    nonce_hex: str,
    tag_hex: str,
    receiver_secret_key: bytes,
) -> bytes:
    """
    Decrypt a stored encrypted file.

    Steps:
    1. Decapsulate shared secret from KEM ciphertext using receiver's secret key
    2. Read encrypted bytes from disk
    3. Decrypt with AES-256-GCM
    4. Return raw decrypted bytes (NEVER written to a temp file)

    Args:
        stored_filename: The UUID-based filename in the uploads directory.
        kem_ciphertext_hex: Kyber KEM ciphertext (hex-encoded).
        nonce_hex: AES-GCM nonce (hex-encoded).
        tag_hex: AES-GCM authentication tag (hex-encoded).
        receiver_secret_key: Receiver's Kyber512 secret key (raw bytes).

    Returns:
        Raw decrypted file bytes.
    """
    # Step 1: Decapsulate shared secret
    kem_ciphertext = bytes.fromhex(kem_ciphertext_hex)
    shared_secret = decapsulate(receiver_secret_key, kem_ciphertext)

    # Step 2: Read encrypted file from disk
    encrypted_path = os.path.join(UPLOAD_DIR, stored_filename)
    if not os.path.exists(encrypted_path):
        raise FileNotFoundError(f"Encrypted file not found: {stored_filename}")

    with open(encrypted_path, "rb") as f:
        encrypted_bytes = f.read()

    # Step 3: Decrypt with AES-256-GCM
    aes_key = derive_aes_key(shared_secret)
    nonce = bytes.fromhex(nonce_hex)
    tag = bytes.fromhex(tag_hex)
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    decrypted_bytes = cipher.decrypt_and_verify(encrypted_bytes, tag)

    return decrypted_bytes
