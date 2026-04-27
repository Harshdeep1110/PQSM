"""
Module: backend.services.firebase_auth
Purpose: Firebase Authentication integration for the PQC Messenger.
         Verifies Firebase ID tokens on protected routes using firebase-admin SDK.
         Firebase UID becomes the canonical user identifier in production.
Created by: TASK-26 (Phase 7 — Google Cloud Integration)

Usage:
  - Frontend authenticates via Firebase JS SDK (email/password)
  - Frontend sends Firebase ID token to backend in Authorization header
  - Backend verifies the token and extracts the user's UID/email
  - Feature flag: USE_FIREBASE_AUTH=true/false (defaults to false for local dev)
"""

import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature Flag
# ---------------------------------------------------------------------------
USE_FIREBASE_AUTH = os.environ.get("USE_FIREBASE_AUTH", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Firebase Admin SDK Initialization
# ---------------------------------------------------------------------------
_firebase_app = None


def _init_firebase():
    """Initialize the Firebase Admin SDK (once)."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Use GOOGLE_APPLICATION_CREDENTIALS env var (standard GCP auth)
        # or explicitly pass a service account key path
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        project_id = os.environ.get("FIREBASE_PROJECT_ID", os.environ.get("GCP_PROJECT_ID"))

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, {
                "projectId": project_id,
            })
        else:
            # Use Application Default Credentials (works on GCP)
            _firebase_app = firebase_admin.initialize_app(options={
                "projectId": project_id,
            })

        logger.info(f"Firebase Admin SDK initialized for project: {project_id}")
        return _firebase_app

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


# ---------------------------------------------------------------------------
# Token Verification
# ---------------------------------------------------------------------------
def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and extract user claims.

    Args:
        id_token: The Firebase ID token from the frontend.

    Returns:
        dict with: uid, email, name (if available), email_verified

    Raises:
        ValueError: If the token is invalid or expired.
    """
    _init_firebase()

    from firebase_admin import auth

    try:
        decoded = auth.verify_id_token(id_token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "name": decoded.get("name", decoded.get("email", "").split("@")[0]),
            "email_verified": decoded.get("email_verified", False),
        }
    except auth.ExpiredIdTokenError:
        raise ValueError("Firebase token has expired. Please sign in again.")
    except auth.InvalidIdTokenError:
        raise ValueError("Invalid Firebase token.")
    except Exception as e:
        raise ValueError(f"Firebase token verification failed: {e}")


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------
async def get_firebase_user(authorization: str = None) -> dict:
    """
    FastAPI dependency that extracts and verifies a Firebase ID token
    from the Authorization header (Bearer <token>).

    Returns:
        dict with: uid, email, name, email_verified

    Raises:
        HTTPException 401 if token is missing or invalid.
    """
    from fastapi import HTTPException

    if not USE_FIREBASE_AUTH:
        # In local dev mode, skip Firebase auth
        return None

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required.")

    # Extract Bearer token
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format. Use: Bearer <token>")

    try:
        return verify_firebase_token(parts[1])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
