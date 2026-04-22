# PQC Messenger — Deployment Guide

> Step-by-step instructions for deploying the Post-Quantum Secure Messenger
> to the cloud using **Render.com** (backend) and **Vercel** (frontend).

---

## 1. Prerequisites

- [ ] **GitHub repository** — Push all code to a GitHub repo
- [ ] **Render.com account** — [sign up free](https://render.com) (free tier works)
- [ ] **Vercel account** — [sign up free](https://vercel.com) (free tier works)
- [ ] **Python 3.10+** and **Node 18+** installed locally for testing

---

## 2. Deploy Backend on Render

### Step 2.1 — Create a New Web Service

1. Log into [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Select the repo containing `pqc-messenger`

### Step 2.2 — Configure the Service

| Setting | Value |
|---------|-------|
| **Name** | `pqc-messenger-backend` |
| **Region** | Choose closest to your users |
| **Runtime** | **Docker** |
| **Dockerfile Path** | `backend/Dockerfile` |
| **Docker Context** | `.` (project root) |

### Step 2.3 — Add a Persistent Disk

> SQLite and uploaded files need persistent storage that survives deploys.

1. Scroll to **Disks** section
2. Click **Add Disk**
3. **Name:** `pqc-data`
4. **Mount Path:** `/data`
5. **Size:** 1 GB (expandable later)

### Step 2.4 — Set Environment Variables

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `/data/pqc_messenger.db` |
| `UPLOAD_DIR` | `/data/uploads` |
| `SECRET_KEY` | Click "Generate" for a random value |
| `MAX_FILE_SIZE_MB` | `50` |
| `ALLOWED_ORIGINS` | Your Vercel URL (set after Step 3) |

### Step 2.5 — Deploy

1. Click **Create Web Service**
2. Wait for the Docker build to complete (~3-5 minutes first time)
3. Your backend URL will be: `https://pqc-messenger-backend.onrender.com`

> **Note:** The free tier spins down after 15 minutes of inactivity.
> First request after sleep takes ~30 seconds (cold start). This is acceptable for a demo.

---

## 3. Deploy Frontend on Vercel

### Step 3.1 — Import Project

1. Log into [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import your GitHub repository

### Step 3.2 — Configure Build Settings

| Setting | Value |
|---------|-------|
| **Root Directory** | `frontend` |
| **Framework Preset** | Vite |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### Step 3.3 — Add Environment Variables

| Variable | Value |
|----------|-------|
| `VITE_BACKEND_URL` | `https://pqc-messenger-backend.onrender.com` |
| `VITE_BACKEND_WS_URL` | `wss://pqc-messenger-backend.onrender.com` |

> **Important:** WebSocket over TLS requires `wss://` not `ws://`.
> Render provides TLS termination automatically.

### Step 3.4 — Deploy

1. Click **Deploy**
2. Wait for the build (~1-2 minutes)
3. Your frontend URL will be: `https://pqc-messenger.vercel.app` (or similar)

### Step 3.5 — Update Render CORS

Go back to your Render service and update the `ALLOWED_ORIGINS` env var:

```
ALLOWED_ORIGINS=https://pqc-messenger.vercel.app
```

Redeploy the backend for the change to take effect.

---

## 4. Post-Deploy Checklist

After both services are live, verify the following:

- [ ] **Health check:** Visit `https://your-backend.onrender.com/` — should return JSON with service info
- [ ] **User registration:** `POST /register` with a username and password
- [ ] **Chat test:** Open two browser tabs on the Vercel URL, register as Alice and Bob, send messages
- [ ] **File upload:** Send an image file — verify it appears in the chat
- [ ] **Encryption Visualizer:** Verify the side panel shows crypto trace for both text and file messages
- [ ] **CORS:** Verify that only the Vercel domain is allowed (no wildcard in production)

---

## 5. Known Limitations (Free Tier)

### Render (Backend)

| Limit | Detail |
|-------|--------|
| **RAM** | 512 MB — Kyber512/ML-DSA-44 are lightweight enough to run |
| **CPU** | 0.1 CPU — sufficient for demo workloads |
| **Sleep** | Service sleeps after 15 min inactivity — first message after sleep ~30s |
| **Disk** | 1 GB persistent disk included — expand in dashboard if needed |
| **Bandwidth** | 100 GB/month |

> **Tip:** Larger parameter sets (Kyber1024, ML-DSA-87) may be slow on 0.1 CPU.
> Kyber512 + ML-DSA-44 are the lightest and recommended for demo.

### Vercel (Frontend)

| Limit | Detail |
|-------|--------|
| **Hosting** | Purely static — no server-side logic |
| **Bandwidth** | 100 GB/month |
| **Builds** | 6000 minutes/month |

---

## 6. Alternative: Run Locally

If you prefer to run everything locally:

```bash
# Terminal 1: Backend
cd pqc-messenger
python -m uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd pqc-messenger/frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 7. Troubleshooting

### liboqs build fails on Render
- Ensure you're using the **Docker** runtime, not bare Python
- The Dockerfile installs `cmake`, `gcc`, `g++`, `make`, `libssl-dev`
- If build still fails, check Render build logs for specific errors

### WebSocket connection fails in production
- Ensure frontend uses `wss://` (not `ws://`) in `VITE_BACKEND_WS_URL`
- Render provides TLS automatically, but the client must use the secure protocol

### CORS errors
- Verify `ALLOWED_ORIGINS` on Render matches your exact Vercel URL
- Include the full URL with `https://` prefix
- Multiple origins can be comma-separated

### File uploads fail
- Check `MAX_FILE_SIZE_MB` env var (default: 50)
- Verify `UPLOAD_DIR` points to the persistent disk mount (`/data/uploads`)
- Ensure the uploaded file's MIME type is in the allowlist
