# PQC Messenger — Post-Quantum Secure Messaging System

A **software-only** post-quantum secure messaging system using CRYSTALS-Kyber (key exchange), ML-DSA-44/Dilithium (digital signatures), and AES-256-GCM (symmetric encryption). Features a live **Encryption Visualizer** that shows the full cryptographic pipeline in real-time.

## Algorithms

| Purpose            | Algorithm     | Standard          | Security Level     |
|--------------------|---------------|-------------------|--------------------|
| Key Exchange       | Kyber512      | NIST FIPS 203     | 128-bit PQ         |
| Digital Signatures | ML-DSA-44     | NIST FIPS 204     | 128-bit PQ         |
| Symmetric Encrypt  | AES-256-GCM   | NIST SP 800-38D   | 256-bit classical  |

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for the React frontend)
- **liboqs** native library (see installation below)

### Installing liboqs (Windows)

```bash
# Option 1: Build from source (recommended)
git clone https://github.com/open-quantum-safe/liboqs.git
cd liboqs && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=../install ..
cmake --build . --config Release
cmake --install . --config Release

# Option 2: Use pre-built binaries if available
# Check: https://github.com/open-quantum-safe/liboqs/releases

# Then install the Python wrapper:
pip install liboqs-python
```

### Installing Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Installing Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the Application

### 1. Start the Backend

```bash
# From the project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. You can view the auto-generated docs at `http://localhost:8000/docs`.

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 3. Demo: Encrypted Chat

1. Open **Tab 1** → Go to `http://localhost:5173` → Enter username `Alice` → Click "Generate Keys & Connect"
2. Open **Tab 2** → Go to `http://localhost:5173` → Enter username `Bob` → Click "Generate Keys & Connect"
3. In Alice's tab, click on **Bob** in the sidebar
4. Type a message and click **🔐 Send**
5. Watch the **Encryption Visualizer** panel on the right side show the full crypto pipeline!

## How It Works

```
┌──────────┐                                         ┌──────────┐
│  Alice   │                                         │   Bob    │
│ (Sender) │                                         │(Receiver)│
└────┬─────┘                                         └────┬─────┘
     │                                                    │
     │  1. Type plaintext message                         │
     │  ─────────────────────────                         │
     │                                                    │
     │  2. Kyber512 KEM: Encapsulate shared secret        │
     │     using Bob's public key                         │
     │     → shared_secret + kem_ciphertext               │
     │                                                    │
     │  3. AES-256-GCM: Encrypt plaintext                 │
     │     with shared_secret                             │
     │     → ciphertext + nonce + auth_tag                │
     │                                                    │
     │  4. ML-DSA-44: Sign the ciphertext                 │
     │     with Alice's signing key                       │
     │     → signature                                    │
     │                                                    │
     │  ═══════════════════════════════════════════►       │
     │  Send: kem_ct + ciphertext + nonce + tag + sig     │
     │                                                    │
     │                     5. Kyber512: Decapsulate        │
     │                        → recover shared_secret     │
     │                                                    │
     │                     6. ML-DSA-44: Verify signature  │
     │                        → confirm Alice is sender    │
     │                                                    │
     │                     7. AES-256-GCM: Decrypt         │
     │                        → recover plaintext ✓       │
     └────────────────────────────────────────────────────┘
```

## API Endpoints

| Method | Endpoint                   | Description                          |
|--------|----------------------------|--------------------------------------|
| GET    | `/`                        | Health check                         |
| POST   | `/register`                | Register new user (returns keys)     |
| GET    | `/users`                   | List all registered users            |
| GET    | `/messages/{user_a}/{user_b}` | Fetch encrypted message history   |
| WS     | `/ws/{username}`           | WebSocket for real-time messaging    |

## Running Tests

```bash
python -m pytest backend/tests/test_e2e.py -v
```

The test suite covers:
- Health check & API endpoints
- User registration & duplicate detection
- Kyber512 KEM roundtrip
- AES-256-GCM encrypt/decrypt roundtrip
- ML-DSA-44 sign/verify (including tamper detection)
- Full encryption pipeline (Alice → Bob end-to-end)
- WebSocket connection & authentication
- WebSocket ping/pong keepalive

## Project Structure

```
pqc-messenger/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLite + SQLAlchemy setup
│   ├── models.py            # Pydantic data models
│   ├── crypto/
│   │   ├── kyber.py         # Kyber512 key encapsulation
│   │   ├── aes_gcm.py       # AES-256-GCM encryption
│   │   └── dilithium.py     # ML-DSA-44 digital signatures
│   ├── messaging/
│   │   ├── ws_handler.py    # WebSocket handler + encryption pipeline
│   │   └── message_store.py # Encrypted message persistence
│   ├── auth/
│   │   └── user_manager.py  # User registration & key management
│   └── tests/
│       └── test_e2e.py      # End-to-end integration tests
├── frontend/
│   └── src/
│       ├── App.jsx                          # Main app + login
│       ├── components/
│       │   ├── ChatWindow.jsx               # Message display
│       │   ├── MessageInput.jsx             # Message composer
│       │   ├── UserList.jsx                 # Online users sidebar
│       │   ├── EncryptionVisualizer.jsx     # ⭐ Crypto pipeline viewer
│       │   └── KeyExchangeStatus.jsx        # Security status badge
│       ├── hooks/
│       │   └── useWebSocket.js              # WebSocket connection hook
│       └── utils/
│           └── cryptoUtils.js               # Hex formatting utilities
└── README.md
```

## Tech Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + SQLite
- **Frontend:** React 19 + Vite 8
- **Cryptography:** liboqs 0.15.0 (CRYSTALS-Kyber512, ML-DSA-44) + pycryptodome (AES-256-GCM)
- **Transport:** WebSocket (FastAPI native)
