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

# PQC Messaging System — Phase 5 & 6 Extension

> **Instructions for the agent reading this:**
> This document extends the original workflow. The same `AGENT_LOCK.md` and `PROJECT_STATE.md`
> coordination rules apply. Tasks are numbered starting from TASK-15 to avoid collisions with the
> original 14 tasks. All Phase 1–4 tasks must be marked `[✓]` in AGENT_LOCK.md before any
> Phase 5 or Phase 6 task is started.

---

## 🔄 Updated Project File Structure (Delta from original)

The following new files and directories are added to the existing structure.
Do not reorganize existing files — only append.

```
pqc-messenger/
├── backend/
│   ├── media/                          # NEW
│   │   ├── __init__.py
│   │   ├── file_handler.py             # Upload, encrypt, save to disk
│   │   └── file_store.py              # DB records for uploaded files
│   ├── uploads/                        # NEW — local disk storage for encrypted files
│   │   └── .gitkeep
│   ├── main.py                         # MODIFIED — add media REST endpoints
│   ├── database.py                     # MODIFIED — add media_files table
│   └── requirements.txt               # MODIFIED — add python-magic, aiofiles
├── frontend/
│   └── src/
│       └── components/
│           ├── MediaUpload.jsx         # NEW — file picker + send button
│           ├── MediaMessage.jsx        # NEW — renders image/video/audio in chat
│           └── EncryptionVisualizer.jsx # MODIFIED — add media crypto trace display
├── deploy/                             # NEW
│   ├── render.yaml                     # Backend deployment config (Render.com)
│   ├── vercel.json                     # Frontend deployment config (Vercel)
│   ├── .env.example                    # Environment variable template
│   └── DEPLOY_GUIDE.md                # Step-by-step deployment instructions
├── .gitignore                          # NEW/MODIFIED — exclude uploads/, .env
└── PROJECT_STATE.md                    # MODIFIED — update to reflect Phase 5/6
```

---

## ✅ PHASE 5 — File & Media Sharing

> **Prerequisite:** TASK-01 through TASK-14 must all be `[✓]` in AGENT_LOCK.md.

---

### TASK-15: Database Schema Extension for Media

- [ ] Open `backend/database.py` (do NOT rewrite it — append only)
- [ ] Add new table `media_files`:
  - `id` (UUID, primary key)
  - `sender` (string, FK to users.username)
  - `receiver` (string, FK to users.username)
  - `file_type` (string: `image` | `video` | `audio` | `document`)
  - `original_filename` (string — sanitized, no path traversal)
  - `stored_filename` (string — UUID-based name used on disk)
  - `encrypted_path` (string — relative path under `backend/uploads/`)
  - `file_size_bytes` (integer)
  - `nonce_hex` (string — AES-GCM nonce for this file)
  - `tag_hex` (string — AES-GCM auth tag)
  - `kem_ciphertext_hex` (string — Kyber encapsulated key for this file)
  - `signature_hex` (string — Dilithium signature over encrypted file bytes)
  - `timestamp` (datetime)
- [ ] Run migration / recreate DB schema
- [ ] Update `backend/models.py` — add `MediaFileRecord` Pydantic model
- **Dependencies:** TASK-05 complete
- **Output files:** `backend/database.py` (modified), `backend/models.py` (modified)

---

### TASK-16: Server-Side File Handler

- [ ] Implement `backend/media/file_handler.py`
- [ ] Implement `encrypt_and_store_file(file_bytes: bytes, filename: str, sender: str, receiver_public_key: bytes, sender_sign_key: bytes) → dict`:
  - [ ] Generate a fresh Kyber KEM pair for this file (one-time use)
  - [ ] Encapsulate a shared secret using receiver's Kyber public key
  - [ ] Encrypt file bytes with AES-256-GCM using the shared secret
  - [ ] Sign the encrypted bytes with sender's Dilithium key
  - [ ] Save the encrypted bytes to `backend/uploads/{uuid}.enc`
  - [ ] Return a dict: `{stored_filename, nonce_hex, tag_hex, kem_ciphertext_hex, signature_hex, file_size_bytes}`
- [ ] Implement `decrypt_file(stored_filename: str, kem_ciphertext_hex: str, nonce_hex: str, tag_hex: str, receiver_secret_key: bytes) → bytes`:
  - [ ] Decapsulate shared secret from kem_ciphertext using receiver's secret key
  - [ ] Decrypt the stored `.enc` file
  - [ ] Return raw decrypted bytes
- [ ] **Security rules to enforce:**
  - [ ] Sanitize filenames — strip path separators, reject `..`
  - [ ] Enforce max file size: 50MB
  - [ ] Allowed MIME types only: `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `video/mp4`, `video/webm`, `audio/mpeg`, `audio/ogg`, `audio/wav`
  - [ ] Reject all other MIME types with HTTP 415
- **Dependencies:** TASK-15, TASK-02, TASK-03, TASK-04 complete
- **Output files:** `backend/media/file_handler.py`, `backend/media/__init__.py`

---

### TASK-17: File Store & Media DB Operations

- [ ] Implement `backend/media/file_store.py`
- [ ] Implement `save_media_record(sender, receiver, file_type, original_filename, stored_filename, file_size_bytes, nonce_hex, tag_hex, kem_ciphertext_hex, signature_hex) → media_id`
- [ ] Implement `get_media_record(media_id: str) → MediaFileRecord`
- [ ] Implement `get_media_history(user_a: str, user_b: str) → list[MediaFileRecord]`
- [ ] The server stores only encrypted bytes — plaintext file content must never be written to disk
- **Dependencies:** TASK-15 complete
- **Output files:** `backend/media/file_store.py`

---

### TASK-18: Backend REST Endpoints for Media

- [ ] Open `backend/main.py` — add the following endpoints (do not rewrite existing endpoints):
- [ ] `POST /upload` — multipart form upload:
  - [ ] Accept: `file` (UploadFile), `sender` (str), `receiver` (str)
  - [ ] Call `file_handler.encrypt_and_store_file()`
  - [ ] Call `file_store.save_media_record()`
  - [ ] Return: `{media_id, file_type, original_filename, file_size_bytes, timestamp}`
  - [ ] Also push a WebSocket notification to receiver: `{type: "media_message", media_id, sender, file_type, original_filename}`
- [ ] `GET /media/{media_id}` — download/stream decrypted file:
  - [ ] Accepts query param: `receiver_username`
  - [ ] Fetches media record, decrypts file using receiver's stored secret key
  - [ ] Returns decrypted bytes as `StreamingResponse` with correct Content-Type header
  - [ ] **Important:** decrypted bytes are streamed — never written to a temp file
- [ ] `GET /media/history/{user_a}/{user_b}` — returns list of `MediaFileRecord` JSON
- [ ] Update CORS config if needed for multipart
- **Dependencies:** TASK-16, TASK-17, TASK-08 complete
- **Output files:** `backend/main.py` (modified)

---

### TASK-19: Frontend — Media Upload Component

- [ ] Implement `frontend/src/components/MediaUpload.jsx`
- [ ] Render a paperclip / attach icon button next to `MessageInput`
- [ ] On click: open a file picker filtered to images, video (mp4/webm), audio (mp3/ogg/wav)
- [ ] Show a preview before sending:
  - [ ] Images: `<img>` thumbnail
  - [ ] Video: `<video>` preview (muted, 3s)
  - [ ] Audio: `<audio>` player
- [ ] On confirm send:
  - [ ] POST to `/upload` as multipart form
  - [ ] Show upload progress bar (use `XMLHttpRequest` with `onprogress`)
  - [ ] On success: push the `media_id` into the chat window
- [ ] On error: show inline error message (file too large, unsupported type, etc.)
- [ ] Add upload state to `useWebSocket.js` hook: `sendMediaMessage(file, receiver)`
- **Dependencies:** TASK-09, TASK-10, TASK-18 complete
- **Output files:** `frontend/src/components/MediaUpload.jsx`, `frontend/src/hooks/useWebSocket.js` (modified)

---

### TASK-20: Frontend — Media Message Renderer

- [ ] Implement `frontend/src/components/MediaMessage.jsx`
- [ ] Receives props: `{media_id, file_type, original_filename, sender, timestamp}`
- [ ] Fetches decrypted file from `GET /media/{media_id}?receiver_username={currentUser}` on mount
- [ ] Renders based on `file_type`:
  - [ ] `image` → `<img>` with lightbox (click to expand)
  - [ ] `video` → `<video controls>` with playback controls
  - [ ] `audio` → custom styled `<audio>` player (waveform optional)
- [ ] Shows a "🔐 Encrypted at rest" badge below each media item
- [ ] Shows file name + size in a caption
- [ ] Integrate into `ChatWindow.jsx` — messages of type `media_message` render `<MediaMessage>` instead of plain text
- **Dependencies:** TASK-19, TASK-10 complete
- **Output files:** `frontend/src/components/MediaMessage.jsx`, `frontend/src/components/ChatWindow.jsx` (modified)

---

### TASK-21: Extend Encryption Visualizer for Media

- [ ] Open `frontend/src/components/EncryptionVisualizer.jsx`
- [ ] Add a new tab or section: **"File Encryption Trace"**
- [ ] When a media message is sent or received, display:
  - [ ] File name + type + size
  - [ ] Step 1 — Original file size in bytes (pre-encryption)
  - [ ] Step 2 — Kyber512 KEM: truncated `kem_ciphertext_hex`
  - [ ] Step 3 — AES-256-GCM: nonce, auth tag, encrypted size
  - [ ] Step 4 — Dilithium2 signature: truncated `signature_hex`
  - [ ] Step 5 — "Decryption verified ✓" (confirmed by successful download)
- [ ] Reuse the existing arrow-flow visualization design — extend it, don't replace it
- **Dependencies:** TASK-20, TASK-11 complete
- **Output files:** `frontend/src/components/EncryptionVisualizer.jsx` (modified)

---

## ✅ PHASE 6 — Cloud Deployment

> **Prerequisite:** TASK-15 through TASK-21 must all be `[✓]` in AGENT_LOCK.md.
> Phase 6 tasks are mostly configuration and documentation — they do not change application logic.

---

### TASK-22: Environment Variable Extraction

- [ ] Audit all hardcoded values across the codebase and replace with environment variables:
  - [ ] `DATABASE_URL` — SQLite path (e.g. `/data/pqc_messenger.db` for Render persistent disk)
  - [ ] `UPLOAD_DIR` — absolute path to uploads folder (e.g. `/data/uploads` on Render)
  - [ ] `ALLOWED_ORIGINS` — comma-separated list of allowed CORS origins (e.g. your Vercel URL)
  - [ ] `SECRET_KEY` — a random string for signing sessions (generate with `secrets.token_hex(32)`)
  - [ ] `MAX_FILE_SIZE_MB` — default 50
  - [ ] `FRONTEND_URL` — set to Vercel deployment URL after TASK-24
- [ ] Use `python-dotenv` in `backend/main.py` to load `.env` on startup
- [ ] Create `deploy/.env.example` with all variable names and placeholder values (no real secrets)
- [ ] Create/update `.gitignore` — ensure `.env`, `backend/uploads/*`, `*.db` are excluded
- **Dependencies:** TASK-18 complete
- **Output files:** `deploy/.env.example`, `.gitignore`, `backend/main.py` (modified)

---

### TASK-23: Render.com Backend Deployment Config

- [ ] Create `deploy/render.yaml` — Render Blueprint file:
  ```yaml
  services:
    - type: web
      name: pqc-messenger-backend
      runtime: python
      buildCommand: pip install -r backend/requirements.txt
      startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
      envVars:
        - key: DATABASE_URL
          value: /data/pqc_messenger.db
        - key: UPLOAD_DIR
          value: /data/uploads
        - key: SECRET_KEY
          generateValue: true
        - key: MAX_FILE_SIZE_MB
          value: 50
      disk:
        name: pqc-data
        mountPath: /data
        sizeGB: 1
  ```
- [ ] Verify `backend/requirements.txt` includes all dependencies including `liboqs-python` install note
- [ ] Add a `backend/Dockerfile` as an alternative deploy method (Render supports Docker):
  - [ ] Base image: `python:3.11-slim`
  - [ ] Install system deps needed for liboqs: `cmake`, `gcc`, `libssl-dev`
  - [ ] Copy backend, install requirements, expose port 8000
  - [ ] CMD: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- [ ] **Note in comments:** liboqs-python requires native compilation. Render's free tier supports this via Docker. The Dockerfile is the recommended deploy path.
- **Dependencies:** TASK-22 complete
- **Output files:** `deploy/render.yaml`, `backend/Dockerfile`

---

### TASK-24: Vercel Frontend Deployment Config

- [ ] Create `deploy/vercel.json`:
  ```json
  {
    "buildCommand": "npm run build",
    "outputDirectory": "build",
    "installCommand": "npm install",
    "framework": "create-react-app",
    "rewrites": [
      { "source": "/(.*)", "destination": "/index.html" }
    ]
  }
  ```
- [ ] Update `frontend/src/hooks/useWebSocket.js`:
  - [ ] WebSocket URL must read from `process.env.REACT_APP_BACKEND_WS_URL` (fallback: `ws://localhost:8000`)
  - [ ] All `fetch` calls must read from `process.env.REACT_APP_BACKEND_URL` (fallback: `http://localhost:8000`)
- [ ] Create `frontend/.env.example`:
  ```
  REACT_APP_BACKEND_URL=https://your-render-app.onrender.com
  REACT_APP_BACKEND_WS_URL=wss://your-render-app.onrender.com
  ```
- [ ] Add `frontend/.env.local` to `.gitignore`
- [ ] Verify the React build works: `cd frontend && npm run build` must exit 0 with no errors
- **Dependencies:** TASK-22 complete
- **Output files:** `deploy/vercel.json`, `frontend/.env.example`, `frontend/src/hooks/useWebSocket.js` (modified)

---

### TASK-25: Deployment Guide Document

- [ ] Create `deploy/DEPLOY_GUIDE.md` with the following sections:

#### Section 1 — Prerequisites
- GitHub repo (code must be pushed)
- Render.com account (free tier works)
- Vercel account (free tier works)

#### Section 2 — Deploy Backend on Render
- Step-by-step: New Web Service → Connect GitHub → Select Docker runtime → Set env vars → Deploy
- Explain the persistent disk setup (`/data`) for SQLite + uploads
- Explain that the free tier spins down after 15min inactivity (cold start ~30s) — acceptable for demo
- Note the deployed URL format: `https://pqc-messenger-backend.onrender.com`

#### Section 3 — Deploy Frontend on Vercel
- Step-by-step: Import Git repo → Set root to `frontend/` → Add env vars (`REACT_APP_BACKEND_URL`, `REACT_APP_BACKEND_WS_URL`) → Deploy
- Note: WebSocket over TLS requires `wss://` not `ws://` — Render provides TLS automatically

#### Section 4 — Post-Deploy Checklist
- [ ] Test user registration via `POST /register`
- [ ] Test chat between two browser tabs
- [ ] Test file upload (image, then audio)
- [ ] Verify Encryption Visualizer shows crypto trace
- [ ] Verify CORS allows only the Vercel domain in production

#### Section 5 — Known Limitations (Free Tier)
- Render free tier: 512MB RAM, 0.1 CPU — Kyber512/Dilithium2 are lightweight enough to run; larger parameter sets (Kyber1024) may be slow
- Render free tier: service sleeps after inactivity — first message after sleep may take ~30s
- Upload storage: 1GB persistent disk included; expand in Render dashboard if needed
- Vercel: no server-side logic, purely static hosting for the React build

- **Dependencies:** TASK-23, TASK-24 complete
- **Output files:** `deploy/DEPLOY_GUIDE.md`

---

## 🔒 Updated AGENT_LOCK.md Rows to Add

When claiming any Phase 5 or 6 task, append a row following the existing format:

```
| TASK-15  | Agent-X-SessY   | IN_PROGRESS | DB schema extension     |
| TASK-16  | Agent-X-SessY   | DONE        | file_handler.py done    |
...
```

---

## 📋 Updated PROJECT_STATE.md Addition

When Phase 5 begins, add this section to PROJECT_STATE.md:

```
## Phase 5 — Media Sharing
- TASK-15: [ ]
- TASK-16: [ ]
- TASK-17: [ ]
- TASK-18: [ ]
- TASK-19: [ ]
- TASK-20: [ ]
- TASK-21: [ ]

## Phase 6 — Cloud Deployment
- TASK-22: [ ]
- TASK-23: [ ]
- TASK-24: [ ]
- TASK-25: [ ]
```

---

## ⚠️ Critical Notes for All Agents in Phase 5 & 6

1. **Never store plaintext file bytes on disk.** Only `.enc` (AES-GCM encrypted) files go into `backend/uploads/`. Decryption happens in-memory during the `GET /media/{id}` stream.

2. **Each file gets its own fresh KEM operation.** Do not reuse the chat session's shared secret for file encryption. File encryption uses a one-time Kyber encapsulation specifically for that file.

3. **liboqs-python requires native compilation.** On Render, use the Dockerfile path (TASK-23). Do not attempt pip install on a bare Python environment without the system build deps.

4. **WebSocket upgrades require `wss://` in production.** Render provides TLS termination automatically. Ensure frontend env vars use `wss://` not `ws://` when pointing to the Render URL.

5. **TASK-21 modifies EncryptionVisualizer** — agent doing TASK-21 must coordinate with TASK-11 completion. Do not start TASK-21 until TASK-11 is `[✓]` and no other agent has TASK-21 claimed.