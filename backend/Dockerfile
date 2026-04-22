# PQC Messenger Backend — Dockerfile
# Purpose: Docker image for deploying the backend on Render.com (or any Docker host).
# Created by: TASK-23
#
# liboqs-python requires native compilation, so we install build dependencies
# (cmake, gcc, libssl-dev) before pip install.

FROM python:3.11-slim

# Install system dependencies required for building liboqs from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    gcc \
    g++ \
    make \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the backend source code
COPY backend/ /app/backend/

# Create uploads directory
RUN mkdir -p /data/uploads

# Expose port 8000
EXPOSE 8000

# Environment defaults (can be overridden at runtime)
ENV DATABASE_URL=/data/pqc_messenger.db
ENV UPLOAD_DIR=/data/uploads
ENV MAX_FILE_SIZE_MB=50

# Start the FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
