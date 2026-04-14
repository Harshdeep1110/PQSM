"""
Module: backend.auth.user_manager
Purpose: User registration, authentication, and key management.
         Generates Kyber + ML-DSA-44 keypairs, stores public keys in the database,
         and returns private keys to the caller (one-time delivery).
Created by: TASK-05

Security model:
  - Passwords hashed with PBKDF2-SHA256 + random salt (never stored in plaintext)
  - Public keys stored server-side (for encryption/verification by other users)
  - Private keys returned to client at registration and NEVER stored on server
"""

import hashlib
import os

from sqlalchemy.orm import Session

from backend.database import UserRecord
from backend.crypto.kyber import generate_keypair as kyber_generate_keypair
from backend.crypto.dilithium import generate_signing_keypair


# ---------------------------------------------------------------------------
# Password Hashing Utilities
# ---------------------------------------------------------------------------
def _hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """
    Hash a password using PBKDF2-SHA256 with a random salt.

    Args:
        password: Plaintext password.
        salt: Optional salt bytes. If None, a random 32-byte salt is generated.

    Returns:
        (password_hash_hex, salt_hex) tuple.
    """
    if salt is None:
        salt = os.urandom(32)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=100_000,
    )
    return pw_hash.hex(), salt.hex()


def _verify_password(password: str, stored_hash_hex: str, stored_salt_hex: str) -> bool:
    """
    Verify a password against a stored PBKDF2-SHA256 hash.

    Args:
        password: Plaintext password to verify.
        stored_hash_hex: The stored password hash (hex-encoded).
        stored_salt_hex: The stored salt (hex-encoded).

    Returns:
        True if the password matches, False otherwise.
    """
    salt = bytes.fromhex(stored_salt_hex)
    computed_hash, _ = _hash_password(password, salt)
    return computed_hash == stored_hash_hex


# ---------------------------------------------------------------------------
# User Registration
# ---------------------------------------------------------------------------
def register_user(db: Session, username: str, password: str) -> dict:
    """
    Register a new user with password and post-quantum keypairs.

    Steps:
    1. Check if username already exists
    2. Hash the password with PBKDF2-SHA256
    3. Generate a Kyber512 keypair (for key exchange / encryption)
    4. Generate an ML-DSA-44 keypair (for digital signatures)
    5. Store password hash + public keys in the database
    6. Return private keys to the caller (one-time only!)

    Args:
        db: SQLAlchemy database session.
        username: Desired username (must be unique).
        password: Account password (will be hashed before storage).

    Returns:
        dict with username, public keys (hex), and private keys (hex).

    Raises:
        ValueError: If username is already taken.
    """
    # Check for existing user
    existing = db.query(UserRecord).filter(UserRecord.username == username).first()
    if existing:
        raise ValueError(f"Username '{username}' is already registered.")

    # Hash the password with a random salt
    pw_hash_hex, pw_salt_hex = _hash_password(password)

    # Generate Kyber512 keypair (KEM — key encapsulation)
    kyber_public, kyber_secret = kyber_generate_keypair()

    # Generate ML-DSA-44 keypair (signatures)
    dilithium_verify, dilithium_sign = generate_signing_keypair()

    # Store password hash + public keys in the database
    user = UserRecord(
        username=username,
        password_hash=pw_hash_hex,
        password_salt=pw_salt_hex,
        public_key_kyber=kyber_public,
        public_key_dilithium=dilithium_verify,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Return everything — private keys are delivered ONE TIME ONLY
    return {
        "username": username,
        "public_key_kyber_hex": kyber_public.hex(),
        "verify_key_dilithium_hex": dilithium_verify.hex(),
        "secret_key_kyber_hex": kyber_secret.hex(),
        "sign_key_dilithium_hex": dilithium_sign.hex(),
    }


# ---------------------------------------------------------------------------
# User Lookup
# ---------------------------------------------------------------------------
def get_user(db: Session, username: str) -> UserRecord | None:
    """
    Fetch a user record by username.

    Args:
        db: SQLAlchemy database session.
        username: The username to look up.

    Returns:
        UserRecord or None if not found.
    """
    return db.query(UserRecord).filter(UserRecord.username == username).first()


# ---------------------------------------------------------------------------
# List All Users
# ---------------------------------------------------------------------------
def list_users(db: Session) -> list[dict]:
    """
    List all registered users with their public keys.

    Returns:
        List of dicts with username and public key hex strings.
    """
    users = db.query(UserRecord).all()
    return [
        {
            "username": u.username,
            "public_key_kyber_hex": u.public_key_kyber.hex(),
            "verify_key_dilithium_hex": u.public_key_dilithium.hex(),
            "created_at": u.created_at,
        }
        for u in users
    ]


# ---------------------------------------------------------------------------
# Key + Password Verification (Login)
# ---------------------------------------------------------------------------
def verify_user_keys(
    db: Session,
    username: str,
    password: str,
    secret_key_kyber_hex: str,
    sign_key_dilithium_hex: str,
) -> dict:
    """
    Authenticate a returning user by verifying password AND private keys.

    Steps:
    1. Look up user in the database
    2. Verify password against stored PBKDF2-SHA256 hash
    3. Perform Kyber KEM round-trip to verify the private key matches the public key

    Args:
        db: SQLAlchemy database session.
        username: The username to verify.
        password: Plaintext password provided by the client.
        secret_key_kyber_hex: Kyber512 secret key (hex-encoded) provided by the client.
        sign_key_dilithium_hex: ML-DSA-44 signing key (hex-encoded) provided by the client.

    Returns:
        dict with username and public keys if verification succeeds.

    Raises:
        ValueError: If user not found, password wrong, or keys don't match.
    """
    from backend.crypto.kyber import encapsulate, decapsulate

    user = db.query(UserRecord).filter(UserRecord.username == username).first()
    if not user:
        raise ValueError(f"User '{username}' is not registered.")

    # Step 1: Verify password
    if not _verify_password(password, user.password_hash, user.password_salt):
        raise ValueError("Invalid password.")

    # Step 2: Verify Kyber private key via KEM round-trip
    try:
        secret_key = bytes.fromhex(secret_key_kyber_hex)
        test_ciphertext, test_shared_secret = encapsulate(user.public_key_kyber)
        recovered_secret = decapsulate(secret_key, test_ciphertext)

        if test_shared_secret != recovered_secret:
            raise ValueError("Kyber key verification failed — shared secrets do not match.")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Key verification failed: {e}")

    return {
        "username": username,
        "public_key_kyber_hex": user.public_key_kyber.hex(),
        "verify_key_dilithium_hex": user.public_key_dilithium.hex(),
    }
