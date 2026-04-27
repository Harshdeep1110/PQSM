#!/bin/bash
# PQC Messenger — Manual Cloud Run Deployment Script
# Created by: TASK-31 (Phase 7)
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. GCP project set: gcloud config set project pqsm-18197
#   3. APIs enabled: Cloud Run, Container Registry, Firestore, Cloud Storage, Cloud Logging
#   4. GCS bucket created: gsutil mb gs://pqsm-18197-encrypted-data

set -e

PROJECT_ID="${GCP_PROJECT_ID:-pqsm-18197}"
REGION="us-central1"
SERVICE_NAME="pqc-messenger-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=== PQC Messenger — Cloud Run Deployment ==="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Step 1: Build Docker image
echo "[1/3] Building Docker image..."
docker build -t "${IMAGE_NAME}:latest" -f backend/Dockerfile .

# Step 2: Push to Container Registry
echo "[2/3] Pushing to Container Registry..."
docker push "${IMAGE_NAME}:latest"

# Step 3: Deploy to Cloud Run
echo "[3/3] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}:latest" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --timeout=300 \
    --session-affinity \
    --min-instances=0 \
    --max-instances=3 \
    --memory=1Gi \
    --cpu=1 \
    --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
    --set-env-vars="STORAGE_BACKEND=firestore" \
    --set-env-vars="USE_FIREBASE_AUTH=true" \
    --set-env-vars="ENABLE_AUDIT_LOGGING=true" \
    --set-env-vars="ENABLE_KMS=false" \
    --set-env-vars="GCS_BUCKET_NAME=pqsm-18197-encrypted-data" \
    --set-env-vars="ALLOWED_ORIGINS=*"

echo ""
echo "=== Deployment Complete ==="
echo "Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format="value(status.url)"
