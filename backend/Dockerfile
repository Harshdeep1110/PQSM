# PQC Messenger Backend — Dockerfile for Google Cloud Run
# Pre-builds liboqs from source so the native library is available at runtime.

FROM python:3.11-slim

# Install ALL build dependencies (needed to compile liboqs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    gcc \
    g++ \
    make \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Step 1: Clone and build liboqs from source
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git && \
    cd liboqs && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DBUILD_SHARED_LIBS=ON \
          -DOQS_BUILD_ONLY_LIB=ON \
          .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Verify liboqs is installed
RUN ls -la /usr/local/lib/liboqs* && ldconfig -p | grep oqs

WORKDIR /app

# Step 2: Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Step 3: Verify oqs can be imported
RUN python -c "import oqs; print('liboqs loaded successfully:', oqs.oqs.oqs_version())"

# Step 4: Copy backend source
COPY backend/ /app/backend/

# Create directories
RUN mkdir -p /data/uploads

# Ensure the dynamic linker can find liboqs
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

EXPOSE 8080
ENV PORT=8080
ENV DATABASE_URL=/data/pqc_messenger.db
ENV UPLOAD_DIR=/data/uploads

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
