"""Security and Cryptographic State Token Engine.

Handles Google OIDC Bearer Token verification and HMAC-SHA256 stateless
state token generation and validation for 48+ hour Human-In-The-Loop (HITL) workflows.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
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

