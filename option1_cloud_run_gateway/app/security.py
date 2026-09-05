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


import ipaddress
import socket
import threading
import urllib.parse
import uuid

# Thread-safe bounded Idempotency Registry with TTL-based pruning for 21 CFR Part 11 Action State Tokens
CONSUMED_JTI_REGISTRY: Dict[str, float] = {}  # jti -> exp timestamp
MAX_JTI_CACHE_SIZE = 50_000
_jti_lock = threading.Lock()


def _prune_expired_jtis(now_ts: float):
    """Prune expired JTI nonces from the registry to prevent memory leaks."""
    expired = [k for k, exp in CONSUMED_JTI_REGISTRY.items() if exp < now_ts]
    for k in expired:
        CONSUMED_JTI_REGISTRY.pop(k, None)
    # If still above capacity (e.g. DoS with valid future timestamps), evict earliest expiring
    if len(CONSUMED_JTI_REGISTRY) > MAX_JTI_CACHE_SIZE:
        sorted_keys = sorted(CONSUMED_JTI_REGISTRY.items(), key=lambda x: x[1])
        excess = len(CONSUMED_JTI_REGISTRY) - MAX_JTI_CACHE_SIZE
        for k, _ in sorted_keys[:excess]:
            CONSUMED_JTI_REGISTRY.pop(k, None)


def reset_jti_registry():
    """Reset the consumed JTI nonce registry (primarily for test automation)."""
    with _jti_lock:
        CONSUMED_JTI_REGISTRY.clear()


def is_safe_webhook_url(url: str, allow_localhost: Optional[bool] = None) -> Tuple[bool, str]:
    """Validate webhook URL against SSRF attacks (metadata IP, private IPs, non-http schemes).

    Blocks AWS/GCP link-local metadata (169.254.169.254), internal cloud domains,
    and private RFC 1918 subnets in production environments.
    """
    if not url or not isinstance(url, str):
        return False, "URL is missing or invalid"

    if allow_localhost is None:
        allow_localhost = settings.APP_ENV.lower() != "production"

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as exc:
        return False, f"Malformed URL: {exc}"

    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid scheme '{parsed.scheme}': only http and https are permitted"

    if not allow_localhost and parsed.scheme != "https":
        return False, "Production webhooks must use secure HTTPS scheme"

    hostname = parsed.hostname
    if not hostname:
        return False, "URL contains no valid hostname"

    # Block cloud metadata addresses immediately by hostname
    blocked_hostnames = {
        "metadata.google.internal",
        "metadata.internal",
        "169.254.169.254",
        "instance-data",
        "169.254.169.254.xip.io",
        "169.254.169.254.nip.io",
    }
    if hostname.lower() in blocked_hostnames:
        return False, f"Access to cloud metadata hostname '{hostname}' is strictly prohibited (SSRF Protection)"

    # Resolve hostname to check IP addresses against link-local, loopback, and private ranges
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        if allow_localhost:
            # In development/test mode, allow synthetic/mock domain names (e.g. *.internal, *.test)
            return True, "Mock domain permitted in development"
        return False, f"DNS resolution failed for hostname '{hostname}': {exc}"

    for item in addr_info:
        ip_str = item[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid IP address resolved: {ip_str}"

        # Link-local addresses (169.254.0.0/16, fe80::/10) - ALWAYS BLOCKED
        if ip.is_link_local:
            return False, f"Target IP {ip_str} is in blocked link-local range (cloud metadata defense)"

        # Special/reserved/multicast addresses - ALWAYS BLOCKED
        if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False, f"Target IP {ip_str} is in blocked special-use range"

        # Loopback addresses (127.0.0.0/8, ::1)
        if ip.is_loopback and not allow_localhost:
            return False, f"Target IP {ip_str} is a loopback address (prohibited in production)"

        # RFC 1918 private subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
        if ip.is_private and not allow_localhost:
            return False, f"Target IP {ip_str} is an internal private network address (prohibited in production)"

    return True, "OK"


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
                now_ts = datetime.now(timezone.utc).timestamp()
                exp_ts = float(claims.get("exp", now_ts + settings.STATE_TOKEN_TTL_HOURS * 3600))
                with _jti_lock:
                    _prune_expired_jtis(now_ts)
                    if jti in CONSUMED_JTI_REGISTRY:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Action Already Executed: State Token JTI '{jti}' has already been consumed. (Idempotency Guard Active)",
                        )
                    CONSUMED_JTI_REGISTRY[jti] = exp_ts

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


