"""
Module: backend.crypto.kyber
Purpose: CRYSTALS-Kyber512 Key Encapsulation Mechanism (KEM) using liboqs-python.
         Provides post-quantum secure key exchange — generates keypairs,
         encapsulates shared secrets, and decapsulates them.
Created by: TASK-02

Algorithm: Kyber512 (NIST-selected, lightest parameter set, 128-bit PQ security)
"""

import oqs


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
KYBER_ALGORITHM = "Kyber512"


# ---------------------------------------------------------------------------
# Key Generation
# ---------------------------------------------------------------------------
def generate_keypair() -> tuple[bytes, bytes]:
    """
    Generate a Kyber512 keypair.

    Returns:
        (public_key, secret_key) — both as raw bytes.
        The public key is shared with communication partners.
        The secret key must be kept private.
    """
    # Create a KEM instance for Kyber512
    kem = oqs.KeyEncapsulation(KYBER_ALGORITHM)

    # Generate the keypair — secret key is stored internally,
    # public key is returned
    public_key = kem.generate_keypair()
    secret_key = kem.export_secret_key()

    return (bytes(public_key), bytes(secret_key))


# ---------------------------------------------------------------------------
# Encapsulation (Sender side)
# ---------------------------------------------------------------------------
def encapsulate(public_key: bytes) -> tuple[bytes, bytes]:
    """
    Encapsulate a shared secret using the recipient's public key.

    This is what the SENDER does:
    1. Takes the recipient's public key
    2. Produces a ciphertext (to send to recipient) and a shared secret (to keep)

    Args:
        public_key: The recipient's Kyber512 public key.

    Returns:
        (ciphertext, shared_secret) — both as raw bytes.
        Send the ciphertext to the recipient.
        Use the shared_secret as the symmetric encryption key.
    """
    kem = oqs.KeyEncapsulation(KYBER_ALGORITHM)

    # Encapsulate: produces ciphertext + shared secret from the public key
    ciphertext, shared_secret = kem.encap_secret(public_key)

    return (bytes(ciphertext), bytes(shared_secret))


# ---------------------------------------------------------------------------
# Decapsulation (Receiver side)
# ---------------------------------------------------------------------------
def decapsulate(secret_key: bytes, ciphertext: bytes) -> bytes:
    """
    Decapsulate the shared secret using the receiver's secret key.

    This is what the RECEIVER does:
    1. Takes their own secret key + the ciphertext from the sender
    2. Recovers the same shared secret that the sender derived

    Args:
        secret_key: The receiver's Kyber512 secret key.
        ciphertext: The ciphertext produced by encapsulate().

    Returns:
        shared_secret as raw bytes — should match the sender's shared_secret.
    """
    kem = oqs.KeyEncapsulation(KYBER_ALGORITHM, secret_key)

    # Decapsulate: recovers the shared secret from ciphertext + secret key
    shared_secret = kem.decap_secret(ciphertext)

    return bytes(shared_secret)


# ---------------------------------------------------------------------------
# Self-test / Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Kyber512 KEM — Key Encapsulation Demo")
    print("=" * 60)

    # Step 1: Bob generates a keypair
    print("\n[1] Bob generates a Kyber512 keypair...")
    bob_public, bob_secret = generate_keypair()
    print(f"    Public key : {bob_public[:16].hex()}... ({len(bob_public)} bytes)")
    print(f"    Secret key : {bob_secret[:16].hex()}... ({len(bob_secret)} bytes)")

    # Step 2: Alice encapsulates a shared secret using Bob's public key
    print("\n[2] Alice encapsulates a shared secret using Bob's public key...")
    ciphertext, alice_shared = encapsulate(bob_public)
    print(f"    Ciphertext    : {ciphertext[:16].hex()}... ({len(ciphertext)} bytes)")
    print(f"    Shared secret : {alice_shared.hex()}")

    # Step 3: Bob decapsulates the shared secret using his secret key
    print("\n[3] Bob decapsulates using his secret key + ciphertext...")
    bob_shared = decapsulate(bob_secret, ciphertext)
    print(f"    Shared secret : {bob_shared.hex()}")

    # Step 4: Verify both sides derived the same shared secret
    print("\n[4] Verification:")
    if alice_shared == bob_shared:
        print("    ✅ SUCCESS — Both parties derived the same shared secret!")
    else:
        print("    ❌ FAILURE — Shared secrets do NOT match!")

    print("\n" + "=" * 60)
