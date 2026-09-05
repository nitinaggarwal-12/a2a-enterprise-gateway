"""Security and Cryptographic State Token Engine.

Handles Google OIDC Bearer Token verification and HMAC-SHA256 stateless
state token generation and validation for 48+ hour Human-In-The-Loop (HITL) workflows.
"""

import hmac
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple
from fastapi import Header, HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import JWTError, jwt

from .config import settings


def verify_google_oidc(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify Google OIDC ID token from Authorization Bearer header.

    In APP_ENV=development, allows mock/dev authorization tokens to pass.
    In production, verifies token against Google's public certs and EXPECTED_AUDIENCE.
    """
    if not authorization:
        if settings.APP_ENV.lower() == "development":
            return {"sub": "dev-user@enterprise.internal", "email": "dev-user@enterprise.internal", "aud": "dev-audience"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Development bypass mode
    if settings.APP_ENV.lower() == "development":
        if token.startswith("mock-dev-token") or token == "dev-secret-token" or token == "test-token":
            return {"sub": "dev-user@enterprise.internal", "email": "dev-user@enterprise.internal", "aud": settings.EXPECTED_AUDIENCE}

    try:
        req = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            token,
            req,
            audience=settings.EXPECTED_AUDIENCE,
        )
        return id_info
    except Exception as exc:
        if settings.APP_ENV.lower() == "development":
            # In dev, allow parsing unverified claims if valid JWT format
            try:
                unverified = jwt.get_unverified_claims(token)
                return unverified
            except Exception:
                return {"sub": "dev-fallback@enterprise.internal", "email": "dev-fallback@enterprise.internal"}

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google OIDC token validation failed: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


import threading
import uuid

# Thread-safe atomic Idempotency Registry for 21 CFR Part 11 Action State Tokens
CONSUMED_JTI_REGISTRY = set()
_jti_lock = threading.Lock()


def reset_jti_registry():
    """Reset the consumed JTI nonce registry (primarily for test automation)."""
    with _jti_lock:
        CONSUMED_JTI_REGISTRY.clear()


def create_state_token(payload: Dict[str, Any], ttl_hours: Optional[int] = None, jti: Optional[str] = None) -> str:
    """Create an HMAC-SHA256 sealed stateless JWT token containing clinical task context.

    Payload typically includes: taskId, studyId, cohort, decision, pushUrl.
    Includes iat (issued at), exp (expires at), and cryptographic jti (task nonce) claims.
    """
    ttl = ttl_hours if ttl_hours is not None else settings.STATE_TOKEN_TTL_HOURS
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=ttl)

    token_data = dict(payload)
    if "jti" not in token_data:
        token_data["jti"] = jti or f"jti-a2ui-{uuid.uuid4().hex[:16]}"

    token_data.update({
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": settings.SERVICE_NAME,
    })

    signed_token = jwt.encode(
        token_data,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return signed_token


def verify_state_token(token: str, enforce_idempotency: bool = False) -> Dict[str, Any]:
    """Verify the integrity, signature, and expiration of a stateless state token.

    Raises HTTP 400 Bad Request on tampering, invalid signature, or expiration.
    If enforce_idempotency=True, checks if the jti was already consumed and marks it.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State token is required and must be a string",
        )

    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if enforce_idempotency:
            jti = claims.get("jti")
            if jti:
                with _jti_lock:
                    if jti in CONSUMED_JTI_REGISTRY:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Action Already Executed: State Token JTI '{jti}' has already been consumed. (Idempotency Guard Active)",
                        )
                    CONSUMED_JTI_REGISTRY.add(jti)

        return claims
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State token has expired. HITL approval window exceeded.",
        )
    except HTTPException:
        raise
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tampered or invalid state token signature: {str(exc)}",
        )


def consume_state_token(token: str) -> Dict[str, Any]:
    """Atomically verify and consume a state token for execution.

    Replay attempts with the same token result in HTTP 409 Conflict.
    """
    return verify_state_token(token, enforce_idempotency=True)


class CFRPart11Signer:
    """Stateless cryptographic signer satisfying 21 CFR Part 11 rules:
    - § 11.50 (Manifestation of Signatures: printed name, timestamp, meaning)
    - § 11.70 (Signature/Record Linking: SHA-256 digest of clinical payload)
    - § 11.200 / 11.300 (Credentials: Double-envelope HMAC key authentication)
    """

    SUPPORTED_MEANINGS = [
        "ProtocolApproval",
        "CohortValidation",
        "SafetyReview",
        "SystemAudit",
        "DoseTitrationApproval",
        "DeviationJustification",
    ]

    def __init__(self, hmac_secret_key: Optional[bytes] = None):
        if hmac_secret_key is None:
            hmac_secret_key = settings.JWT_SECRET.encode("utf-8")
        elif not isinstance(hmac_secret_key, bytes):
            if isinstance(hmac_secret_key, str):
                hmac_secret_key = hmac_secret_key.encode("utf-8")
            else:
                raise TypeError("hmac_secret_key must be bytes or str")
        self.secret_key = hmac_secret_key

    def create_signature_payload(
        self,
        agent_id: str,
        agent_name: str,
        meaning: str,
        document_id: str,
        document_data: bytes,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates a 21 CFR Part 11 compliant metadata payload and signs it."""
        if isinstance(document_data, str):
            document_data = document_data.encode("utf-8")
        elif not isinstance(document_data, bytes):
            document_data = json.dumps(document_data, sort_keys=True).encode("utf-8")

        document_hash = hashlib.sha256(document_data).hexdigest()

        payload = {
            "signer_id": agent_id,
            "signer_name": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meaning": meaning,
            "document_id": document_id,
            "document_hash": document_hash,
        }
        if extra_metadata:
            payload["extra_metadata"] = extra_metadata

        serialized_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = hmac.new(self.secret_key, serialized_payload, hashlib.sha256).hexdigest()

        return {
            "payload": payload,
            "signature": signature,
        }

    def verify_signature(self, signed_envelope: Dict[str, Any]) -> Tuple[bool, str]:
        """Statelessly verifies the signature integrity of the incoming package."""
        payload = signed_envelope.get("payload")
        provided_signature = signed_envelope.get("signature")

        if not payload or not provided_signature:
            return False, "Missing payload or signature in envelope"

        required_fields = ["signer_id", "signer_name", "timestamp", "meaning", "document_id", "document_hash"]
        for field in required_fields:
            if field not in payload:
                return False, f"Non-compliant envelope: missing § 11.50 attribute '{field}'"

        serialized_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
        expected_signature = hmac.new(self.secret_key, serialized_payload, hashlib.sha256).hexdigest()

        is_valid = hmac.compare_digest(expected_signature, provided_signature)
        if not is_valid:
            return False, "Cryptographic signature mismatch: record altered in transit"

        return True, "21 CFR Part 11 Signature verified statelessly"


