# PQC Messenger Backend — Dockerfile for Google Cloud Run
# Purpose: Docker image optimized for Cloud Run serverless containers.
# Created by: TASK-23, Modified by: TASK-31 (Phase 7 — Cloud Run)
#
# liboqs-python requires native compilation (cmake, gcc, libssl-dev).
# Cloud Run provides HTTP/2 which supports WebSocket connections.

FROM python:3.11-slim AS builder

# Install system dependencies for building liboqs from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    gcc \
    g++ \
    make \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# --- Runtime stage ---
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the backend source code
COPY backend/ /app/backend/

# Create directories
RUN mkdir -p /data/uploads /app/secrets

# Expose port (Cloud Run injects PORT env var, default 8080)
EXPOSE 8080

# Environment defaults (overridden by Cloud Run env vars / Secret Manager)
ENV DATABASE_URL=/data/pqc_messenger.db
ENV UPLOAD_DIR=/data/uploads
ENV MAX_FILE_SIZE_MB=50
ENV PORT=8080
ENV STORAGE_BACKEND=sqlite
ENV USE_FIREBASE_AUTH=false
ENV ENABLE_KMS=false
ENV ENABLE_AUDIT_LOGGING=false

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')"

# Start FastAPI — use PORT env var from Cloud Run
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
