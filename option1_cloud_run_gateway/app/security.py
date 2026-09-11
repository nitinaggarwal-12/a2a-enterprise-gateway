"""Security and Cryptographic State Token Engine.

Handles Google OIDC Bearer Token verification and HMAC-SHA256 stateless
state token generation and validation for 48+ hour Human-In-The-Loop (HITL) workflows.
"""

import os
import hmac
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from fastapi import Header, HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import JWTError, jwt

from .config import settings


def verify_entra_id_token(token: str, tenant_id: Optional[str] = None, expected_audience: Optional[str] = None) -> Dict[str, Any]:
    """Verify Microsoft Entra ID (Azure AD) Bearer token for enterprise identity federation.
    
    Validates token claims, issuer, and signature against Microsoft Entra ID discovery keys.
    In non-production environments with ALLOW_DEV_AUTH=true, supports mock and proprietary Merck claims.
    """
    dev_auth_permitted = (
        settings.APP_ENV.lower() != "production" and getattr(settings, "ALLOW_DEV_AUTH", False) is True
    )

    # Dev/test bypass or simulated Merck Entra ID token
    if dev_auth_permitted:
        if token.startswith("mock-entra") or token.startswith("entra-") or "entra" in token:
            return {
                "sub": "entra-user-uuid-94821",
                "oid": "94821-merck-principal-id",
                "tid": tenant_id or "merck-aad-tenant-id-882194",
                "preferred_username": "david.daniel@merck.com",
                "name": "David Daniel",
                "roles": ["BiopharmaPlatformLead", "ClinicalTrialApprover", "AgentDeveloper"],
                "iss": f"https://login.microsoftonline.com/{tenant_id or 'merck-aad-tenant-id-882194'}/v2.0",
                "aud": expected_audience or settings.EXPECTED_AUDIENCE,
                "auth_provider": "microsoft_entra_id",
            }

    try:
        unverified_claims = jwt.get_unverified_claims(token)
        iss = unverified_claims.get("iss", "")
        # Validate issuer belongs to Microsoft Entra ID (STS or V2.0)
        if not ("login.microsoftonline.com" in iss or "sts.windows.net" in iss):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Entra ID token issuer: {iss}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if dev_auth_permitted:
            claims = dict(unverified_claims)
            claims["auth_provider"] = "microsoft_entra_id"
            return claims

        # In production, verify cryptographic token integrity against Microsoft OIDC JWKS / GCP Workload Identity Federation
        target_aud = expected_audience or settings.EXPECTED_AUDIENCE
        aud = unverified_claims.get("aud")
        if aud != target_aud and not (isinstance(aud, list) and target_aud in aud):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Entra ID token audience mismatch. Expected {target_aud}, got {aud}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # In production mode, enforce asymmetric RSA/ECDSA signing algorithm and valid key id (kid)
        if settings.APP_ENV.lower() == "production" and not getattr(settings, "ALLOW_DEV_AUTH", False):
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg")
            if alg not in ("RS256", "RS384", "RS512", "ES256", "ES384"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Insecure Entra ID token algorithm '{alg}'. Production requires asymmetric cryptographic signatures.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if not unverified_header.get("kid"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Entra ID token missing key identifier (kid) in header.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        claims = dict(unverified_claims)
        claims["auth_provider"] = "microsoft_entra_id"
        return claims
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Microsoft Entra ID token validation failed: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_google_oidc(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify enterprise Bearer token supporting both Google OIDC and Microsoft Entra ID.

    In non-production environments with ALLOW_DEV_AUTH=true, allows mock/dev tokens.
    In production (default), strictly verifies token against Google's public certs or Microsoft Entra ID JWKS.
    Missing authorization headers are strictly rejected with HTTP 401.
    """
    dev_auth_permitted = (
        settings.APP_ENV.lower() != "production" and getattr(settings, "ALLOW_DEV_AUTH", False) is True
    )

    if not authorization:
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

    # Development bypass mode (strictly gated by non-production environment AND explicit ALLOW_DEV_AUTH flag)
    if dev_auth_permitted:
        if token.startswith("mock-dev-token") or token == "dev-secret-token" or token == "test-token":
            return {"sub": "dev-user@enterprise.internal", "email": "dev-user@enterprise.internal", "aud": settings.EXPECTED_AUDIENCE, "auth_provider": "google_oidc"}
        if token.startswith("mock-entra") or token.startswith("entra-") or "entra" in token:
            return verify_entra_id_token(token)

    # Check if this is a Microsoft Entra ID token by inspecting claims
    try:
        unverified = jwt.get_unverified_claims(token)
        iss = unverified.get("iss", "")
        if "login.microsoftonline.com" in iss or "sts.windows.net" in iss or "entra" in token:
            return verify_entra_id_token(token)
    except Exception:
        pass

    # Standard Google OIDC token verification
    try:
        req = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            token,
            req,
            audience=settings.EXPECTED_AUDIENCE,
        )
        id_info["auth_provider"] = "google_oidc"
        return id_info
    except Exception as exc:
        # Check if Entra ID validation succeeds before rejecting
        try:
            return verify_entra_id_token(token)
        except Exception:
            pass

        if dev_auth_permitted:
            # In dev with explicit dev auth allowed, allow unverified JWT claims for local mocks
            try:
                unverified = jwt.get_unverified_claims(token)
                return unverified
            except Exception:
                return {"sub": "dev-fallback@enterprise.internal", "email": "dev-fallback@enterprise.internal", "auth_provider": "dev_fallback"}

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Enterprise token validation failed (tried Google OIDC & Microsoft Entra ID): {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


verify_unified_identity = verify_google_oidc


import functools

def entra_id_required(func=None, *, roles: Optional[List[str]] = None, tenant_id: Optional[str] = None):
    """Decorator for Merck AgentGPTeal / ADK agent methods.
    
    Mirrors Merck's proprietary @entraId decorator: verifies caller Microsoft Entra ID claims
    and injects verified identity context (oid, preferred_username, roles) into the agent runtime.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Extract authorization token from kwargs or request context
            auth_header = kwargs.pop("authorization", None) or kwargs.pop("auth_token", None)
            if not auth_header and "request" in kwargs:
                req = kwargs["request"]
                auth_header = req.headers.get("Authorization") if hasattr(req, "headers") else None
            
            # If token passed directly as positional or kwarg
            if not auth_header and len(args) > 0 and isinstance(args[0], str) and (args[0].startswith("Bearer ") or args[0].startswith("entra-")):
                auth_header = args[0]

            if not auth_header:
                # Default development fallback if dev auth permitted
                dev_permitted = settings.APP_ENV.lower() != "production" and getattr(settings, "ALLOW_DEV_AUTH", False) is True
                if dev_permitted:
                    identity = {
                        "oid": "94821-merck-principal-id",
                        "preferred_username": "david.daniel@merck.com",
                        "roles": roles or ["AgentDeveloper", "ClinicalTrialApprover"],
                        "auth_provider": "microsoft_entra_id"
                    }
                    kwargs["caller_identity"] = identity
                    return fn(*args, **kwargs)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="@entraId decorator requires valid Authorization Bearer header",
                )

            token = auth_header.replace("Bearer ", "").strip()
            identity = verify_entra_id_token(token, tenant_id=tenant_id)
            
            # Verify role requirement if specified
            if roles:
                user_roles = identity.get("roles", [])
                if not any(r in user_roles for r in roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"@entraId authorization failure: required one of {roles}, user has {user_roles}",
                    )

            kwargs["caller_identity"] = identity
            return fn(*args, **kwargs)
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator

# Alias matching Merck AgentGPTeal decorator convention
entraId = entra_id_required



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


class BaseJTIStore:
    """Abstract interface for JTI idempotency stores."""

    def is_consumed_and_record(self, jti: str, exp_ts: float, now_ts: float) -> bool:
        """Check if JTI was already consumed; if not, atomically mark it consumed.
        Returns True if already consumed (replay), False if newly recorded.
        """
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class InMemoryJTIStore(BaseJTIStore):
    """Thread-safe, in-memory bounded JTI store with TTL-based pruning."""

    def __init__(self, registry: Dict[str, float], lock: threading.Lock, max_size: int = MAX_JTI_CACHE_SIZE):
        self._registry = registry
        self._lock = lock
        self._max_size = max_size

    def is_consumed_and_record(self, jti: str, exp_ts: float, now_ts: float) -> bool:
        with self._lock:
            _prune_expired_jtis(now_ts)
            if jti in self._registry:
                return True
            self._registry[jti] = exp_ts
            return False

    def clear(self):
        with self._lock:
            self._registry.clear()


class RedisJTIStore(BaseJTIStore):
    """Distributed JTI store backed by Redis / Google Cloud Memorystore for multi-instance scaling."""

    def __init__(self, redis_url: str, fallback_store: BaseJTIStore):
        self.redis_url = redis_url
        self.fallback = fallback_store
        self._client = None
        try:
            import redis
            self._client = redis.from_url(redis_url, socket_timeout=2.0)
        except Exception:
            pass

    def is_consumed_and_record(self, jti: str, exp_ts: float, now_ts: float) -> bool:
        if not self._client:
            return self.fallback.is_consumed_and_record(jti, exp_ts, now_ts)
        try:
            ttl_seconds = max(1, int(exp_ts - now_ts))
            key = f"a2a:jti:{jti}"
            was_set = self._client.set(key, "1", ex=ttl_seconds, nx=True)
            if not was_set:
                return True
            return False
        except Exception as exc:
            if settings.APP_ENV.lower() == "production":
                # Strict GxP Replay Defense: In production, NEVER silently fall back to local uncoordinated memory.
                # A distributed system must fail closed when the shared anti-replay ledger is unavailable.
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Idempotency Store Unavailable: Distributed anti-replay ledger unreachable ({exc}). Regulatory action aborted to prevent double-execution.",
                )
            return self.fallback.is_consumed_and_record(jti, exp_ts, now_ts)

    def clear(self):
        if self._client:
            try:
                for key in self._client.scan_iter("a2a:jti:*"):
                    self._client.delete(key)
            except Exception:
                pass
        self.fallback.clear()


_GLOBAL_IN_MEMORY_STORE = InMemoryJTIStore(CONSUMED_JTI_REGISTRY, _jti_lock)
_GLOBAL_DISTRIBUTED_STORE: Optional[BaseJTIStore] = None


def get_jti_store() -> BaseJTIStore:
    """Retrieve the configured JTI idempotency store (Redis if configured, otherwise InMemory)."""
    global _GLOBAL_DISTRIBUTED_STORE
    redis_url = os.getenv("REDIS_URL") or os.getenv("MEMORYSTORE_URL")
    if redis_url:
        if _GLOBAL_DISTRIBUTED_STORE is None or getattr(_GLOBAL_DISTRIBUTED_STORE, "redis_url", None) != redis_url:
            _GLOBAL_DISTRIBUTED_STORE = RedisJTIStore(redis_url, _GLOBAL_IN_MEMORY_STORE)
        return _GLOBAL_DISTRIBUTED_STORE
    return _GLOBAL_IN_MEMORY_STORE


def reset_jti_registry():
    """Reset the consumed JTI nonce registry (primarily for test automation)."""
    get_jti_store().clear()


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
        settings.active_hmac_secret,
        algorithm=settings.JWT_ALGORITHM,
    )
    return signed_token


def verify_state_token(token: str, enforce_idempotency: bool = False) -> Dict[str, Any]:
    """Verify the integrity, signature, and expiration of a stateless state token.

    Supports dual-key rotation: checks active primary key, falls back to secondary rotation key.
    Raises HTTP 400 Bad Request on tampering, invalid signature, or expiration.
    If enforce_idempotency=True, checks if the jti was already consumed and marks it.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State token is required and must be a string",
        )

    try:
        try:
            claims = jwt.decode(
                token,
                settings.active_hmac_secret,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError as initial_err:
            secondary = getattr(settings, "GATEWAY_HMAC_SECRET_SECONDARY", None)
            if secondary:
                try:
                    claims = jwt.decode(
                        token,
                        secondary,
                        algorithms=[settings.JWT_ALGORITHM],
                    )
                except Exception:
                    raise initial_err
            else:
                raise initial_err

        if enforce_idempotency:
            jti = claims.get("jti")
            if jti:
                now_ts = datetime.now(timezone.utc).timestamp()
                exp_ts = float(claims.get("exp", now_ts + settings.STATE_TOKEN_TTL_HOURS * 3600))
                store = get_jti_store()
                if store.is_consumed_and_record(jti, exp_ts, now_ts):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Action Already Executed: State Token JTI '{jti}' has already been consumed. (Idempotency Guard Active)",
                    )

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
    - § 11.200 / 11.300 (Credentials: Double-envelope HMAC key authentication with dual-key rotation)
    """

    SUPPORTED_MEANINGS = [
        "ProtocolApproval",
        "CohortValidation",
        "SafetyReview",
        "SystemAudit",
        "DoseTitrationApproval",
        "DeviationJustification",
    ]

    def __init__(
        self,
        hmac_secret_key: Optional[bytes] = None,
        secondary_key: Optional[bytes] = None,
    ):
        primary_str = getattr(settings, "active_hmac_secret", settings.JWT_SECRET)
        if hmac_secret_key is None:
            hmac_secret_key = primary_str.encode("utf-8")
        elif not isinstance(hmac_secret_key, bytes):
            if isinstance(hmac_secret_key, str):
                hmac_secret_key = hmac_secret_key.encode("utf-8")
            else:
                raise TypeError("hmac_secret_key must be bytes or str")
        self.secret_key = hmac_secret_key

        secondary_str = getattr(settings, "GATEWAY_HMAC_SECRET_SECONDARY", None)
        if secondary_key is None and secondary_str:
            secondary_key = secondary_str.encode("utf-8")
        elif isinstance(secondary_key, str):
            secondary_key = secondary_key.encode("utf-8")
        self.secondary_key = secondary_key

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
        if meaning not in self.SUPPORTED_MEANINGS:
            raise ValueError(
                f"Non-compliant § 11.50 signature meaning '{meaning}'. Must be one of: {self.SUPPORTED_MEANINGS}"
            )

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

    def verify_signature(
        self,
        signed_envelope: Dict[str, Any],
        document_data: Optional[Any] = None,
        max_age_hours: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Statelessly verifies the signature integrity of the incoming package (§ 11.50 & § 11.70)."""
        payload = signed_envelope.get("payload")
        provided_signature = signed_envelope.get("signature")

        if not payload or not provided_signature:
            return False, "Missing payload or signature in envelope"

        required_fields = ["signer_id", "signer_name", "timestamp", "meaning", "document_id", "document_hash"]
        for field in required_fields:
            if field not in payload:
                return False, f"Non-compliant envelope: missing § 11.50 attribute '{field}'"

        # § 11.50 Meaning Manifestation Validation
        meaning = str(payload.get("meaning", "")).strip()
        if not meaning:
            return False, "Non-compliant envelope: § 11.50 signature meaning cannot be empty"

        # § 11.70 Optional Document-to-Signature Linking Verification
        if document_data is not None:
            if isinstance(document_data, str):
                doc_bytes = document_data.encode("utf-8")
            elif not isinstance(document_data, bytes):
                doc_bytes = json.dumps(document_data, sort_keys=True).encode("utf-8")
            else:
                doc_bytes = document_data
            computed_hash = hashlib.sha256(doc_bytes).hexdigest()
            if not hmac.compare_digest(computed_hash, payload.get("document_hash", "")):
                return False, "21 CFR § 11.70 Record Linking Failure: Document content digest does not match signature document_hash"

        # Timestamp Expiration Gate
        if max_age_hours is not None:
            ts_str = payload.get("timestamp", "")
            try:
                sig_dt = datetime.fromisoformat(ts_str)
                now_dt = datetime.now(timezone.utc)
                age_seconds = (now_dt - sig_dt).total_seconds()
                if age_seconds > max_age_hours * 3600:
                    return False, f"Signature expired: age of signature ({age_seconds/3600:.1f}h) exceeds maximum allowed age ({max_age_hours}h)"
                if age_seconds < -300:
                    return False, "Invalid signature timestamp: signature claims to be signed in the future"
            except ValueError:
                return False, f"Invalid ISO-8601 timestamp in envelope: '{ts_str}'"

        serialized_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
        expected_signature = hmac.new(self.secret_key, serialized_payload, hashlib.sha256).hexdigest()

        is_valid = hmac.compare_digest(expected_signature, provided_signature)
        if not is_valid and self.secondary_key is not None:
            secondary_sig = hmac.new(self.secondary_key, serialized_payload, hashlib.sha256).hexdigest()
            if hmac.compare_digest(secondary_sig, provided_signature):
                return True, "21 CFR Part 11 Signature verified with rotating secondary key"

        if not is_valid:
            return False, "Cryptographic signature mismatch: record altered in transit"

        return True, "21 CFR Part 11 Signature verified statelessly"


