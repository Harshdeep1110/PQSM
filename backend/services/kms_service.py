"""
Module: backend.services.kms_service
Purpose: Cloud KMS stub for envelope encryption (defense in depth).
Created by: TASK-29 (Phase 7)

Status: STUB — set ENABLE_KMS=true to activate real KMS.
"""

import os
import logging

logger = logging.getLogger(__name__)

ENABLE_KMS = os.environ.get("ENABLE_KMS", "false").lower() == "true"
KMS_PROJECT = os.environ.get("GCP_PROJECT_ID", "pqsm-18197")
KMS_LOCATION = os.environ.get("KMS_LOCATION", "global")
KMS_KEY_RING = os.environ.get("KMS_KEY_RING", "pqc-messenger")
KMS_KEY_NAME = os.environ.get("KMS_KEY_NAME", "master-envelope-key")

_kms_client = None


def _get_kms_client():
    global _kms_client
    if _kms_client is not None:
        return _kms_client
    if not ENABLE_KMS:
        return None
    try:
        from google.cloud import kms
        _kms_client = kms.KeyManagementServiceClient()
        logger.info("Cloud KMS client initialized.")
        return _kms_client
    except Exception as e:
        logger.warning(f"Cloud KMS unavailable (stub mode): {e}")
        return None


def _get_key_name() -> str:
    return (
        f"projects/{KMS_PROJECT}/locations/{KMS_LOCATION}"
        f"/keyRings/{KMS_KEY_RING}/cryptoKeys/{KMS_KEY_NAME}"
    )


def envelope_encrypt(plaintext_key: bytes) -> bytes:
    """Wrap a key using Cloud KMS. Returns key unchanged in stub mode."""
    if not ENABLE_KMS:
        return plaintext_key
    client = _get_kms_client()
    if client is None:
        return plaintext_key
    try:
        resp = client.encrypt(request={"name": _get_key_name(), "plaintext": plaintext_key})
        return resp.ciphertext
    except Exception as e:
        logger.error(f"KMS encrypt failed: {e}")
        return plaintext_key


def envelope_decrypt(wrapped_key: bytes) -> bytes:
    """Unwrap a key using Cloud KMS. Returns key unchanged in stub mode."""
    if not ENABLE_KMS:
        return wrapped_key
    client = _get_kms_client()
    if client is None:
        return wrapped_key
    try:
        resp = client.decrypt(request={"name": _get_key_name(), "ciphertext": wrapped_key})
        return resp.plaintext
    except Exception as e:
        logger.error(f"KMS decrypt failed: {e}")
        return wrapped_key


def is_kms_enabled() -> bool:
    return ENABLE_KMS
