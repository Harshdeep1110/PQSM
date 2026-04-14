# Lightweight Post-Quantum Secure Messaging System
## AI Agent Master Prompt & Workflow

---

## ⚠️ CRITICAL INSTRUCTIONS FOR ALL AGENTS

Before starting **any** task:
1. **Read this entire document first.**
2. **Check the `AGENT_LOCK.md` file** in the project root to see which tasks are claimed or completed.
3. **Claim your task** by writing your agent ID + task ID to `AGENT_LOCK.md` before beginning.
4. **Never modify files owned by another agent's task** unless explicitly listed as a dependency step.
5. **When done**, mark your task as `[DONE]` in `AGENT_LOCK.md` and update `PROJECT_STATE.md`.

---

## 🧠 MASTER PROMPT (Copy this into every new agent session)

```
You are a software engineer working on a Lightweight Post-Quantum Secure Messaging System.
This is a SOFTWARE-ONLY project. There is NO external hardware (no ESP32, no Raspberry Pi).
All code runs on a standard desktop/laptop (assume modern CPU, 8GB+ RAM).

The tech stack is:
- Backend: Python (FastAPI or Flask)
- Frontend: React (web browser UI)
- Cryptography: liboqs-python (Open Quantum Safe) for CRYSTALS-Kyber (key exchange) and CRYSTALS-Dilithium (signatures)
- Transport: WebSocket for real-time messaging
- Storage: SQLite (lightweight, no external DB server needed)
- Demo: A live "Encryption Visualizer" panel in the UI showing plaintext → ciphertext → decrypted text

Your job is defined by the task assigned to you in the workflow below.
Always read PROJECT_STATE.md and AGENT_LOCK.md before starting.
Follow the file structure defined in this document. Do not invent new top-level directories.
Write clean, commented code. Each file must begin with a comment block stating: module name, purpose, and which task created it.
```

---

## 📁 Agreed Project File Structure

```
pqc-messenger/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── crypto/
│   │   ├── __init__.py
│   │   ├── kyber.py             # Key encapsulation (Kyber KEM)
│   │   ├── aes_gcm.py           # Symmetric encryption (AES-256-GCM)
│   │   └── dilithium.py         # Digital signatures (Dilithium)
│   ├── messaging/
│   │   ├── __init__.py
│   │   ├── ws_handler.py        # WebSocket connection handler
│   │   └── message_store.py     # SQLite message persistence
│   ├── auth/
│   │   ├── __init__.py
│   │   └── user_manager.py      # User registration & key storage
│   ├── models.py                # Pydantic data models
│   ├── database.py              # SQLite setup
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageInput.jsx
│   │   │   ├── UserList.jsx
│   │   │   ├── EncryptionVisualizer.jsx   # KEY DEMO COMPONENT
│   │   │   └── KeyExchangeStatus.jsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.js
│   │   ├── utils/
│   │   │   └── cryptoUtils.js
│   │   └── styles/
│   │       └── main.css
│   └── package.json
├── AGENT_LOCK.md                # ← Agents must read/write this
├── PROJECT_STATE.md             # ← Current progress summary
└── README.md
```

---

## ✅ MASTER TASK CHECKLIST

> **Status codes:** `[ ]` = Not started | `[→]` = In progress (claimed) | `[✓]` = Done | `[!]` = Blocked

---

### PHASE 1 — Project Scaffold & Cryptography Core
*These tasks must be completed before Phase 2 begins.*

#### TASK-01: Project Initialization
- [ ] Create the full directory structure listed above
- [ ] Create `backend/requirements.txt` with: `fastapi`, `uvicorn`, `websockets`, `liboqs-python`, `pycryptodome`, `sqlalchemy`, `python-dotenv`
- [ ] Create `frontend/package.json` with React, react-scripts, axios, UUID
- [ ] Create `AGENT_LOCK.md` with template (Task ID | Agent ID | Status)
- [ ] Create `PROJECT_STATE.md` with initial state
- [ ] Create `README.md` with setup instructions (how to install liboqs, run backend, run frontend)
- **Output files:** All scaffold files
- **Blocks:** All other tasks

---

#### TASK-02: Kyber Key Encapsulation Module
- [ ] Implement `backend/crypto/kyber.py`
- [ ] Use `liboqs-python` with algorithm `Kyber512` (lightweight variant — appropriate for software-only, no IoT hardware)
- [ ] Implement function: `generate_keypair() → (public_key: bytes, secret_key: bytes)`
- [ ] Implement function: `encapsulate(public_key: bytes) → (ciphertext: bytes, shared_secret: bytes)`
- [ ] Implement function: `decapsulate(secret_key: bytes, ciphertext: bytes) → shared_secret: bytes`
- [ ] Add inline comments explaining what each step does in plain English
- [ ] Write a `__main__` test block that prints a demo of the full KEM cycle
- **Dependencies:** TASK-01 complete
- **Output files:** `backend/crypto/kyber.py`

---

#### TASK-03: AES-GCM Symmetric Encryption Module
- [ ] Implement `backend/crypto/aes_gcm.py`
- [ ] Use `pycryptodome` AES in GCM mode (256-bit key)
- [ ] Implement function: `encrypt(plaintext: str, shared_secret: bytes) → dict` returning `{ciphertext_hex, nonce_hex, tag_hex}`
- [ ] Implement function: `decrypt(ciphertext_hex: str, nonce_hex: str, tag_hex: str, shared_secret: bytes) → str`
- [ ] The shared_secret from Kyber is used as the AES key (derive using SHA-256 if needed to get 32 bytes)
- [ ] Write a `__main__` test block
- **Dependencies:** TASK-01 complete
- **Output files:** `backend/crypto/aes_gcm.py`

---

#### TASK-04: Dilithium Digital Signature Module
- [ ] Implement `backend/crypto/dilithium.py`
- [ ] Use `liboqs-python` with algorithm `Dilithium2` (lightest variant)
- [ ] Implement function: `generate_signing_keypair() → (verify_key: bytes, sign_key: bytes)`
- [ ] Implement function: `sign_message(message: bytes, sign_key: bytes) → signature: bytes`
- [ ] Implement function: `verify_signature(message: bytes, signature: bytes, verify_key: bytes) → bool`
- [ ] Write a `__main__` test block
- **Dependencies:** TASK-01 complete
- **Output files:** `backend/crypto/dilithium.py`

---

### PHASE 2 — Backend Server
*Requires TASK-01, TASK-02, TASK-03, TASK-04 complete.*

#### TASK-05: Database & User Management
- [ ] Implement `backend/database.py` — SQLite setup using SQLAlchemy
- [ ] Create tables: `users` (id, username, public_key_kyber, public_key_dilithium, created_at), `messages` (id, sender, receiver, ciphertext, nonce, tag, signature, timestamp)
- [ ] Implement `backend/auth/user_manager.py`:
  - [ ] `register_user(username) → user_record` — generates Kyber + Dilithium keypairs, stores public keys in DB, returns private keys to caller
  - [ ] `get_user(username) → user_record`
  - [ ] `list_users() → list`
- **Dependencies:** TASK-01 complete
- **Output files:** `backend/database.py`, `backend/auth/user_manager.py`

---

#### TASK-06: Message Store
- [ ] Implement `backend/messaging/message_store.py`
- [ ] Implement function: `save_message(sender, receiver, ciphertext_hex, nonce_hex, tag_hex, signature_hex)`
- [ ] Implement function: `get_messages(user_a, user_b) → list of message dicts`
- [ ] Messages are stored encrypted — the server never stores plaintext
- **Dependencies:** TASK-05 complete
- **Output files:** `backend/messaging/message_store.py`

---

#### TASK-07: WebSocket Handler
- [ ] Implement `backend/messaging/ws_handler.py`
- [ ] Maintain an in-memory dict of active WebSocket connections: `{username: websocket}`
- [ ] On connect: authenticate user, load their private keys from session, send their contact list
- [ ] On message receive (from sender): 
  - [ ] Encapsulate shared secret using receiver's Kyber public key
  - [ ] Encrypt plaintext with AES-GCM using shared secret
  - [ ] Sign the encrypted message with sender's Dilithium key
  - [ ] Forward encrypted package to receiver's WebSocket
  - [ ] Also echo back a `crypto_trace` dict containing: `{plaintext, shared_secret_hex, ciphertext_hex, nonce_hex, tag_hex, signature_hex}` to the **sender only** for the visualizer
- [ ] On message receive (at receiver):
  - [ ] Decapsulate shared secret using receiver's Kyber private key
  - [ ] Verify signature using sender's Dilithium public key
  - [ ] Decrypt ciphertext
  - [ ] Deliver plaintext to UI
  - [ ] Also send `crypto_trace` dict to the **receiver** for the visualizer
- **Dependencies:** TASK-05, TASK-06, TASK-02, TASK-03, TASK-04 complete
- **Output files:** `backend/messaging/ws_handler.py`

---

#### TASK-08: FastAPI Main App
- [ ] Implement `backend/main.py`
- [ ] REST endpoints:
  - [ ] `POST /register` — register new user (returns private keys as JSON, one time only)
  - [ ] `GET /users` — list all registered users
  - [ ] `GET /messages/{user_a}/{user_b}` — fetch message history
- [ ] WebSocket endpoint: `WS /ws/{username}`
- [ ] Mount static frontend build (optional at this stage)
- [ ] Include CORS middleware for local development
- [ ] Include `backend/models.py` Pydantic models for all request/response bodies
- **Dependencies:** TASK-07, TASK-05 complete
- **Output files:** `backend/main.py`, `backend/models.py`

---

### PHASE 3 — Frontend UI
*Requires TASK-08 complete (backend must be runnable).*

#### TASK-09: WebSocket Hook & Crypto Utilities
- [ ] Implement `frontend/src/hooks/useWebSocket.js`
  - [ ] Connect to `ws://localhost:8000/ws/{username}`
  - [ ] Expose: `sendMessage(to, plaintext)`, `messages` state, `cryptoTrace` state
  - [ ] Store the `crypto_trace` from each message in state for the visualizer
- [ ] Implement `frontend/src/utils/cryptoUtils.js`
  - [ ] Utility: `formatHex(bytes)` — truncates long hex strings for display (first 16 chars + "...")
- **Dependencies:** TASK-08 complete
- **Output files:** `frontend/src/hooks/useWebSocket.js`, `frontend/src/utils/cryptoUtils.js`

---

#### TASK-10: Core Chat UI Components
- [ ] Implement `frontend/src/components/UserList.jsx` — shows online users, click to open chat
- [ ] Implement `frontend/src/components/ChatWindow.jsx` — shows message history, sender/receiver labels
- [ ] Implement `frontend/src/components/MessageInput.jsx` — text box + send button
- [ ] Implement `frontend/src/App.jsx` — top level, handles login (username entry), renders layout
- [ ] Basic styling in `frontend/src/styles/main.css` — clean, minimal, dark or light theme
- **Dependencies:** TASK-09 complete
- **Output files:** App.jsx, UserList.jsx, ChatWindow.jsx, MessageInput.jsx, main.css

---

#### TASK-11: Encryption Visualizer Component ⭐ (Demo Feature)
- [ ] Implement `frontend/src/components/EncryptionVisualizer.jsx`
- [ ] This is a **side panel** that appears when a message is sent or received
- [ ] It must clearly display the following **step-by-step** for every message:
  - [ ] **Step 1 — Plaintext:** Show the original message text in green
  - [ ] **Step 2 — Key Exchange:** Show `Kyber512 KEM` label + truncated ciphertext of the encapsulated key
  - [ ] **Step 3 — Encryption:** Show `AES-256-GCM` label + ciphertext hex (truncated) + nonce + auth tag
  - [ ] **Step 4 — Signature:** Show `Dilithium2` label + truncated signature hex
  - [ ] **Step 5 — Decrypted Output:** Show recovered plaintext in green (confirms decryption worked)
  - [ ] Add a visual arrow flow: Plaintext → [Kyber KEM] → [AES-GCM Encrypt] → [Dilithium Sign] → Ciphertext → [Kyber Decap] → [Verify Sig] → [AES-GCM Decrypt] → Plaintext
- [ ] Include a toggle button "Show Encryption Details" / "Hide"
- [ ] Include a "Copy Raw Crypto Data" button that copies the full JSON trace to clipboard
- **Dependencies:** TASK-09, TASK-10 complete
- **Output files:** `frontend/src/components/EncryptionVisualizer.jsx`

---

#### TASK-12: Key Exchange Status Component
- [ ] Implement `frontend/src/components/KeyExchangeStatus.jsx`
- [ ] Small status badge in the chat header: shows `🔐 Kyber512 + Dilithium2` when a secure session is active
- [ ] Shows the truncated public key fingerprint of the current recipient
- [ ] Shows "Key exchange complete" / "Pending" status
- **Dependencies:** TASK-10 complete
- **Output files:** `frontend/src/components/KeyExchangeStatus.jsx`

---

### PHASE 4 — Integration & Demo Polish

#### TASK-13: End-to-End Integration Test Script
- [ ] Create `backend/tests/test_e2e.py`
- [ ] Script that:
  - [ ] Registers two users (Alice and Bob) via REST API
  - [ ] Alice sends Bob a message via WebSocket
  - [ ] Verifies Bob receives the correct decrypted plaintext
  - [ ] Prints the full crypto trace to stdout in a readable format
  - [ ] Asserts the ciphertext is NOT equal to the plaintext (proves encryption works)
- [ ] Run with: `python -m pytest backend/tests/test_e2e.py -v`
- **Dependencies:** TASK-08 complete
- **Output files:** `backend/tests/test_e2e.py`

---

#### TASK-14: README & Demo Instructions
- [ ] Update `README.md` with:
  - [ ] Project overview (2–3 sentences)
  - [ ] Prerequisites: Python 3.10+, Node 18+, liboqs install instructions (pip + native build note)
  - [ ] How to run backend: `uvicorn backend.main:app --reload`
  - [ ] How to run frontend: `npm start` inside `frontend/`
  - [ ] How to demo: Open two browser tabs, register as Alice and Bob, send messages, observe Encryption Visualizer
  - [ ] Algorithm choices and why (Kyber512 = lightweight KEM, Dilithium2 = lightweight sig, AES-256-GCM = fast symmetric)
  - [ ] A "How it works" section with a simple ASCII flow diagram
- **Dependencies:** TASK-13 complete
- **Output files:** `README.md`

---

## 🔒 AGENT_LOCK.md Template

When you begin a task, add a row to this file:

```
| Task ID  | Agent Session ID | Status      | Notes                  |
|----------|-----------------|-------------|------------------------|
| TASK-02  | Agent-A-Sess1   | IN_PROGRESS | Started 2025-xx-xx     |
| TASK-03  | Agent-B-Sess2   | DONE        | kyber.py complete      |
```

---

## 📋 PROJECT_STATE.md Template

```
## Current Phase: PHASE X

## Completed Tasks:
- TASK-01 ✓
- ...

## In Progress:
- TASK-XX (Agent-YY)

## Pending:
- TASK-XX
- ...

## Known Issues / Blockers:
- None

## Notes for Next Agent:
- ...
```

---

## 🎯 Algorithm Selection Rationale (For Agent Reference)

| Purpose            | Algorithm     | Why Chosen                                              |
|--------------------|---------------|---------------------------------------------------------|
| Key Exchange       | Kyber512      | NIST-selected KEM; "512" is the lightweight tier; pure software, fast on desktop |
| Symmetric Encrypt  | AES-256-GCM   | Hardware-accelerated on x86 (AES-NI); fast, authenticated |
| Digital Signatures | Dilithium2    | NIST-selected signature; "2" is lightest parameter set  |
| Transport          | WebSocket     | Low overhead, real-time, no polling                     |
| Storage            | SQLite        | Zero-config, file-based, no server process              |

> **Note:** Kyber768 or Kyber1024 (higher security) are NOT used because they have larger key sizes; Kyber512 provides 128-bit post-quantum security which is sufficient for a demo and keeps the system lightweight.

---

## 🚫 Out of Scope (Do Not Implement)

- Push notifications
- File/media sharing
- Group chats
- Mobile app (React web only)
- External database (PostgreSQL, MongoDB etc.)
- Hardware integration (ESP32, Raspberry Pi, etc.)
- Cloud deployment (localhost only for demo)
