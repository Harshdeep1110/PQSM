"""
Module: backend.crypto.aes_gcm
Purpose: AES-256-GCM authenticated encryption using pycryptodome.
         Encrypts plaintext with a shared secret (from Kyber KEM) and
         returns ciphertext + nonce + authentication tag.
Created by: TASK-03

Algorithm: AES-256-GCM (hardware-accelerated via AES-NI on modern x86 CPUs)
Key derivation: SHA-256 hash of Kyber shared secret → 32-byte AES key
"""

import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


# ---------------------------------------------------------------------------
# Key Derivation
# ---------------------------------------------------------------------------
def derive_aes_key(shared_secret: bytes) -> bytes:
    """
    Derive a 32-byte AES-256 key from the Kyber shared secret.

    The Kyber shared secret may not be exactly 32 bytes, so we hash it
    with SHA-256 to get a consistent 256-bit key for AES.

    Args:
        shared_secret: Raw bytes from the Kyber KEM output.

    Returns:
        32-byte key suitable for AES-256.
    """
    return hashlib.sha256(shared_secret).digest()


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------
def encrypt(plaintext: str, shared_secret: bytes) -> dict:
    """
    Encrypt a plaintext message using AES-256-GCM.

    Steps:
    1. Derive AES key from the shared secret via SHA-256
    2. Generate a random 12-byte nonce (IV)
    3. Encrypt + authenticate the plaintext
    4. Return ciphertext, nonce, and auth tag as hex strings

    Args:
        plaintext: The message string to encrypt.
        shared_secret: The Kyber KEM shared secret (raw bytes).

    Returns:
        dict with keys: ciphertext_hex, nonce_hex, tag_hex
    """
    # Step 1: Derive a 32-byte AES key
    aes_key = derive_aes_key(shared_secret)

    # Step 2: Generate a random 12-byte nonce (recommended size for GCM)
    nonce = get_random_bytes(12)

    # Step 3: Create AES-GCM cipher and encrypt
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))

    # Step 4: Return hex-encoded values for easy transport/storage
    return {
        "ciphertext_hex": ciphertext.hex(),
        "nonce_hex": nonce.hex(),
        "tag_hex": tag.hex(),
    }


# ---------------------------------------------------------------------------
# Decryption
# ---------------------------------------------------------------------------
def decrypt(ciphertext_hex: str, nonce_hex: str, tag_hex: str, shared_secret: bytes) -> str:
    """
    Decrypt and verify an AES-256-GCM encrypted message.

    Steps:
    1. Derive AES key from the shared secret via SHA-256
    2. Convert hex strings back to bytes
    3. Decrypt and verify the authentication tag
    4. Return the original plaintext string

    Args:
        ciphertext_hex: Hex-encoded ciphertext.
        nonce_hex: Hex-encoded nonce/IV.
        tag_hex: Hex-encoded authentication tag.
        shared_secret: The Kyber KEM shared secret (raw bytes).

    Returns:
        Decrypted plaintext string.

    Raises:
        ValueError: If the authentication tag is invalid (tampered data).
    """
    # Step 1: Derive the same AES key
    aes_key = derive_aes_key(shared_secret)

    # Step 2: Convert hex back to raw bytes
    ciphertext = bytes.fromhex(ciphertext_hex)
    nonce = bytes.fromhex(nonce_hex)
    tag = bytes.fromhex(tag_hex)

    # Step 3: Create cipher and decrypt + verify
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)

    # Step 4: Decode and return
    return plaintext_bytes.decode("utf-8")


# ---------------------------------------------------------------------------
# Self-test / Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  AES-256-GCM — Symmetric Encryption Demo")
    print("=" * 60)

    # Simulate a shared secret (in real use, this comes from Kyber KEM)
    fake_shared_secret = get_random_bytes(32)
    message = "Hello, post-quantum world! 🔒"

    print(f"\n[1] Original message : {message}")
    print(f"    Shared secret    : {fake_shared_secret.hex()[:32]}...")

    # Encrypt
    print("\n[2] Encrypting with AES-256-GCM...")
    encrypted = encrypt(message, fake_shared_secret)
    print(f"    Ciphertext : {encrypted['ciphertext_hex'][:32]}...")
    print(f"    Nonce      : {encrypted['nonce_hex']}")
    print(f"    Auth Tag   : {encrypted['tag_hex']}")

    # Decrypt
    print("\n[3] Decrypting...")
    decrypted = decrypt(
        encrypted["ciphertext_hex"],
        encrypted["nonce_hex"],
        encrypted["tag_hex"],
        fake_shared_secret,
    )
    print(f"    Decrypted  : {decrypted}")

    # Verify
    print("\n[4] Verification:")
    if decrypted == message:
        print("    ✅ SUCCESS — Decrypted message matches original!")
    else:
        print("    ❌ FAILURE — Messages do NOT match!")

    # Test tamper detection
    print("\n[5] Tamper detection test...")
    try:
        tampered_ct = "ff" + encrypted["ciphertext_hex"][2:]
        decrypt(tampered_ct, encrypted["nonce_hex"], encrypted["tag_hex"], fake_shared_secret)
        print("    ❌ FAILURE — Tampered data was NOT detected!")
    except ValueError:
        print("    ✅ SUCCESS — Tampered ciphertext correctly rejected!")

    print("\n" + "=" * 60)
