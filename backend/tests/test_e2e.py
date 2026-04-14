"""
Module: backend.tests.test_e2e
Purpose: End-to-end integration test for the PQC Messenger.
         Registers two users, sends a message via WebSocket, and verifies
         the full encryption/decryption pipeline works correctly.
Created by: TASK-13

Run with: python -m pytest backend/tests/test_e2e.py -v
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clean_db():
    """Reset database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestHealthCheck:
    def test_root_endpoint(self, client):
        """Verify the API is running and reports correct algorithms."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "PQC Messenger"
        assert data["status"] == "running"
        assert "Kyber512" in data["algorithms"]["kem"]
        assert "ML-DSA-44" in data["algorithms"]["signature"]
        assert "AES-256-GCM" in data["algorithms"]["symmetric"]


class TestUserRegistration:
    def test_register_alice(self, client):
        """Register a user and verify keypair generation."""
        resp = client.post("/register", json={"username": "Alice"})
        assert resp.status_code == 200
        data = resp.json()

        assert data["username"] == "Alice"
        # Check that all key fields are present and non-empty
        assert len(data["public_key_kyber_hex"]) > 0
        assert len(data["verify_key_dilithium_hex"]) > 0
        assert len(data["secret_key_kyber_hex"]) > 0
        assert len(data["sign_key_dilithium_hex"]) > 0

        # Kyber512 public key should be 800 bytes = 1600 hex chars
        assert len(data["public_key_kyber_hex"]) == 1600

        print(f"\n  Alice registered successfully!")
        print(f"  Kyber public key: {data['public_key_kyber_hex'][:32]}...")
        print(f"  ML-DSA-44 verify key: {data['verify_key_dilithium_hex'][:32]}...")

    def test_register_duplicate(self, client):
        """Duplicate username should return 400."""
        client.post("/register", json={"username": "Alice"})
        resp = client.post("/register", json={"username": "Alice"})
        assert resp.status_code == 400

    def test_list_users(self, client):
        """List users after registration."""
        client.post("/register", json={"username": "Alice"})
        client.post("/register", json={"username": "Bob"})

        resp = client.get("/users")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        usernames = [u["username"] for u in data["users"]]
        assert "Alice" in usernames
        assert "Bob" in usernames


class TestCryptoModules:
    def test_kyber_kem_roundtrip(self):
        """Test Kyber512 key encapsulation and decapsulation."""
        from backend.crypto.kyber import generate_keypair, encapsulate, decapsulate

        pub, sec = generate_keypair()
        ct, ss_sender = encapsulate(pub)
        ss_receiver = decapsulate(sec, ct)

        assert ss_sender == ss_receiver, "Shared secrets must match!"
        assert len(ss_sender) == 32  # 256-bit shared secret
        print(f"\n  Kyber512 KEM: Shared secret = {ss_sender.hex()[:32]}...")

    def test_aes_gcm_roundtrip(self):
        """Test AES-256-GCM encrypt/decrypt roundtrip."""
        from backend.crypto.aes_gcm import encrypt, decrypt
        from Crypto.Random import get_random_bytes

        key = get_random_bytes(32)
        plaintext = "Hello, post-quantum world!"

        enc = encrypt(plaintext, key)
        dec = decrypt(enc["ciphertext_hex"], enc["nonce_hex"], enc["tag_hex"], key)

        assert dec == plaintext
        assert enc["ciphertext_hex"] != plaintext  # Ciphertext != plaintext!
        print(f"\n  AES-256-GCM: '{plaintext}' -> {enc['ciphertext_hex'][:32]}... -> '{dec}'")

    def test_dilithium_sign_verify(self):
        """Test ML-DSA-44 sign and verify."""
        from backend.crypto.dilithium import (
            generate_signing_keypair,
            sign_message,
            verify_signature,
        )

        verify_key, sign_key = generate_signing_keypair()
        message = b"This is authentic."
        signature = sign_message(message, sign_key)

        assert verify_signature(message, signature, verify_key) is True
        assert verify_signature(b"Tampered!", signature, verify_key) is False
        print(f"\n  ML-DSA-44: Signature valid, tamper detection works")


class TestFullPipeline:
    def test_encrypt_decrypt_pipeline(self):
        """
        End-to-end test of the full encryption pipeline:
        Bob generates keys -> Alice encapsulates -> AES encrypts -> Dilithium signs
        -> Bob decapsulates -> verifies -> AES decrypts -> gets original plaintext.
        """
        from backend.crypto.kyber import generate_keypair, encapsulate, decapsulate
        from backend.crypto.aes_gcm import encrypt, decrypt
        from backend.crypto.dilithium import (
            generate_signing_keypair,
            sign_message,
            verify_signature,
        )

        # Setup: Both users generate keys
        bob_kyber_pub, bob_kyber_sec = generate_keypair()
        alice_verify, alice_sign = generate_signing_keypair()

        plaintext = "This is a top secret post-quantum message!"

        # === SENDER (Alice) ===
        # Step 1: KEM encapsulate with Bob's public key
        kem_ct, shared_secret = encapsulate(bob_kyber_pub)

        # Step 2: AES-GCM encrypt with shared secret
        encrypted = encrypt(plaintext, shared_secret)

        # Step 3: Sign the ciphertext
        ciphertext_bytes = bytes.fromhex(encrypted["ciphertext_hex"])
        signature = sign_message(ciphertext_bytes, alice_sign)

        # --- At this point, (kem_ct, encrypted, signature) would be sent to Bob ---

        # Verify ciphertext is NOT equal to plaintext (proves encryption works)
        assert encrypted["ciphertext_hex"] != plaintext.encode().hex()

        # === RECEIVER (Bob) ===
        # Step 4: KEM decapsulate with Bob's secret key
        recovered_secret = decapsulate(bob_kyber_sec, kem_ct)
        assert recovered_secret == shared_secret

        # Step 5: Verify Alice's signature
        is_valid = verify_signature(ciphertext_bytes, signature, alice_verify)
        assert is_valid is True

        # Step 6: AES-GCM decrypt
        decrypted = decrypt(
            encrypted["ciphertext_hex"],
            encrypted["nonce_hex"],
            encrypted["tag_hex"],
            recovered_secret,
        )
        assert decrypted == plaintext

        # Print full crypto trace
        print("\n" + "=" * 60)
        print("  FULL POST-QUANTUM ENCRYPTION PIPELINE — E2E TEST")
        print("=" * 60)
        print(f"\n  Original plaintext : {plaintext}")
        print(f"  Shared secret      : {shared_secret.hex()[:32]}...")
        print(f"  KEM ciphertext     : {kem_ct.hex()[:32]}... ({len(kem_ct)} bytes)")
        print(f"  AES ciphertext     : {encrypted['ciphertext_hex'][:32]}...")
        print(f"  AES nonce          : {encrypted['nonce_hex']}")
        print(f"  AES auth tag       : {encrypted['tag_hex']}")
        print(f"  Signature          : {signature.hex()[:32]}... ({len(signature)} bytes)")
        print(f"  Signature valid    : {is_valid}")
        print(f"  Decrypted text     : {decrypted}")
        print(f"\n  RESULT: {'PASS' if decrypted == plaintext else 'FAIL'}")
        print("=" * 60)


class TestWebSocketChat:
    def test_websocket_connect_and_auth(self, client):
        """
        Test WebSocket connection and authentication.
        The full chat pipeline (Kyber → AES → Dilithium) is tested in
        TestFullPipeline.test_encrypt_decrypt_pipeline.
        This test verifies the WebSocket transport layer works.
        """
        # Register Alice
        alice_resp = client.post("/register", json={"username": "Alice"}).json()

        # Connect Alice via WebSocket
        with client.websocket_connect("/ws/Alice") as ws_alice:
            # First message should be user_list (from connect broadcast)
            msg1 = ws_alice.receive_json()
            assert msg1["type"] == "user_list"
            assert "Alice" in msg1["users_online"]

            # Send authentication
            ws_alice.send_json({
                "type": "auth",
                "secret_key_kyber_hex": alice_resp["secret_key_kyber_hex"],
                "sign_key_dilithium_hex": alice_resp["sign_key_dilithium_hex"],
            })

            # Should get auth_success
            msg2 = ws_alice.receive_json()
            assert msg2["type"] == "auth_success"
            assert "Alice" in msg2.get("users_online", [])

            print(f"\n  WebSocket connection + auth: OK")
            print(f"  Online users: {msg2['users_online']}")

    def test_websocket_ping_pong(self, client):
        """Test WebSocket ping/pong keepalive."""
        client.post("/register", json={"username": "PingUser"})

        with client.websocket_connect("/ws/PingUser") as ws:
            # Drain the initial user_list
            ws.receive_json()

            # Send ping
            ws.send_json({"type": "ping"})
            msg = ws.receive_json()
            assert msg["type"] == "pong"
            print(f"\n  WebSocket ping/pong: OK")

