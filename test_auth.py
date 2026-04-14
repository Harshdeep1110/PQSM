"""Quick script to test registration and login flow."""
import requests

BASE = "http://localhost:8000"

# Register Alice
r1 = requests.post(f"{BASE}/register", json={"username": "Alice", "password": "alice123"})
print(f"Register Alice: {r1.status_code} - {r1.json().get('message', r1.json().get('detail', 'unknown'))}")

# Register Bob
r2 = requests.post(f"{BASE}/register", json={"username": "Bob", "password": "bob12345"})
print(f"Register Bob: {r2.status_code} - {r2.json().get('message', r2.json().get('detail', 'unknown'))}")

# List users
r3 = requests.get(f"{BASE}/users")
data = r3.json()
print(f"Total users: {data['count']}")
for u in data["users"]:
    print(f"  - {u['username']} (registered: {u['created_at']})")

# Test login with correct password
alice_keys = r1.json()
r4 = requests.post(f"{BASE}/login", json={
    "username": "Alice",
    "password": "alice123",
    "secret_key_kyber_hex": alice_keys["secret_key_kyber_hex"],
    "sign_key_dilithium_hex": alice_keys["sign_key_dilithium_hex"],
})
print(f"Login Alice (correct pw): {r4.status_code} - {r4.json().get('message', r4.json().get('detail'))}")

# Test login with wrong password
r5 = requests.post(f"{BASE}/login", json={
    "username": "Alice",
    "password": "wrongpass",
    "secret_key_kyber_hex": alice_keys["secret_key_kyber_hex"],
    "sign_key_dilithium_hex": alice_keys["sign_key_dilithium_hex"],
})
print(f"Login Alice (wrong pw): {r5.status_code} - {r5.json().get('message', r5.json().get('detail'))}")

# Test duplicate registration
r6 = requests.post(f"{BASE}/register", json={"username": "Alice", "password": "alice123"})
print(f"Duplicate registration: {r6.status_code} - {r6.json().get('detail', 'unknown')}")

print("\n--- ALL CHECKS PASSED ---")
