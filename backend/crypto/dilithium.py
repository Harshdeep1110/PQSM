"""
Module: backend.crypto.dilithium
Purpose: ML-DSA-44 (CRYSTALS-Dilithium2) digital signatures using liboqs-python.
         Provides post-quantum secure message authentication — generates
         signing keypairs, signs messages, and verifies signatures.
Created by: TASK-04

Algorithm: ML-DSA-44 (NIST FIPS 204 standardized name for Dilithium2,
           lightest parameter set, 128-bit post-quantum security)
"""

import oqs


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DILITHIUM_ALGORITHM = "ML-DSA-44"  # NIST standardized name (was "Dilithium2")


# ---------------------------------------------------------------------------
# Key Generation
# ---------------------------------------------------------------------------
def generate_signing_keypair() -> tuple[bytes, bytes]:
    """
    Generate an ML-DSA-44 (Dilithium2) signing keypair.

    Returns:
        (verify_key, sign_key) — both as raw bytes.
        The verify_key (public) is shared with communication partners.
        The sign_key (private) is used to sign messages.
    """
    # Create a Signature instance for ML-DSA-44 (Dilithium2)
    signer = oqs.Signature(DILITHIUM_ALGORITHM)

    # Generate keypair — public key returned, secret key stored internally
    verify_key = signer.generate_keypair()
    sign_key = signer.export_secret_key()

    return (bytes(verify_key), bytes(sign_key))


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------
def sign_message(message: bytes, sign_key: bytes) -> bytes:
    """
    Sign a message with the sender's ML-DSA-44 (Dilithium2) private key.

    This proves the message came from the holder of the sign_key.

    Args:
        message: The raw bytes to sign (typically the ciphertext).
        sign_key: The sender's ML-DSA-44 private signing key.

    Returns:
        signature as raw bytes.
    """
    signer = oqs.Signature(DILITHIUM_ALGORITHM, sign_key)

    # Sign the message — produces a detached signature
    signature = signer.sign(message)

    return bytes(signature)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def verify_signature(message: bytes, signature: bytes, verify_key: bytes) -> bool:
    """
    Verify a message signature using the sender's ML-DSA-44 (Dilithium2) public key.

    Args:
        message: The raw bytes that were signed.
        signature: The signature to verify.
        verify_key: The sender's ML-DSA-44 public verification key.

    Returns:
        True if the signature is valid, False otherwise.
    """
    verifier = oqs.Signature(DILITHIUM_ALGORITHM)

    try:
        # Verify returns True if valid, raises exception if invalid
        is_valid = verifier.verify(message, signature, verify_key)
        return is_valid
    except Exception:
        # Any verification failure returns False
        return False


# ---------------------------------------------------------------------------
# Self-test / Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  ML-DSA-44 (Dilithium2) — Digital Signature Demo")
    print("=" * 60)

    # Step 1: Alice generates a signing keypair
    print("\n[1] Alice generates an ML-DSA-44 signing keypair...")
    verify_key, sign_key = generate_signing_keypair()
    print(f"    Verify key : {verify_key[:16].hex()}... ({len(verify_key)} bytes)")
    print(f"    Sign key   : {sign_key[:16].hex()}... ({len(sign_key)} bytes)")

    # Step 2: Alice signs a message
    message = b"Hello Bob, this is a post-quantum signed message!"
    print(f"\n[2] Alice signs the message: {message.decode()}")
    signature = sign_message(message, sign_key)
    print(f"    Signature  : {signature[:16].hex()}... ({len(signature)} bytes)")

    # Step 3: Bob verifies the signature
    print("\n[3] Bob verifies the signature using Alice's verify key...")
    is_valid = verify_signature(message, signature, verify_key)
    if is_valid:
        print("    ✅ SUCCESS — Signature is VALID! Message is authentic.")
    else:
        print("    ❌ FAILURE — Signature is INVALID!")

    # Step 4: Test with tampered message
    print("\n[4] Tamper detection test (modified message)...")
    tampered = b"Hello Bob, this is a TAMPERED message!"
    is_valid_tampered = verify_signature(tampered, signature, verify_key)
    if not is_valid_tampered:
        print("    ✅ SUCCESS — Tampered message correctly rejected!")
    else:
        print("    ❌ FAILURE — Tampered message was NOT detected!")

    # Step 5: Test with wrong key
    print("\n[5] Wrong key test...")
    wrong_verify, _ = generate_signing_keypair()
    is_valid_wrong = verify_signature(message, signature, wrong_verify)
    if not is_valid_wrong:
        print("    ✅ SUCCESS — Wrong verify key correctly rejected!")
    else:
        print("    ❌ FAILURE — Wrong key was NOT detected!")

    print("\n" + "=" * 60)
