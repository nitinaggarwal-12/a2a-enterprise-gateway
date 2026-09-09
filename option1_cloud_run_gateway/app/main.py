"""Cloud Run Interceptor Gateway Main Application.

Stateless FastAPI gateway between Gemini Enterprise (GE) and Enterprise Enterprise Agent Platform.
Provides policy sanitization, authenticated A2A routing, sanitized streaming,
and cryptographic state tokens for Human-in-the-Loop workflows.
"""

import asyncio
import json
import logging
import hashlib
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .config import settings
from .sanitizer import sanitize_a2a_envelope, sanitize_headers, sanitize_payload, sanitize_sse_event
from .security import (
    consume_state_token,
    verify_google_oidc,
    verify_state_token,
    CFRPart11Signer,
    is_safe_webhook_url,
    mint_downstream_id_token,
)
from .a2ui_builder import build_clinical_review_surface
from .a2a_v1 import router as a2a_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle and persistent HTTP connection pools."""
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=200, keepalive_expiry=30.0)
    app.state.http_client = httpx.AsyncClient(limits=limits, timeout=settings.DOWNSTREAM_TIMEOUT_SECONDS)
    logger.info("Shared httpx.AsyncClient connection pool initialized.")
    yield
    if hasattr(app.state, "http_client") and not app.state.http_client.is_closed:
        await app.state.http_client.aclose()
        logger.info("Shared httpx.AsyncClient connection pool closed.")


# Configure Structured JSON Logging
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "service": settings.SERVICE_NAME,
        }
        if hasattr(record, "extra_data"):
            log_obj["extra"] = record.extra_data
        return json.dumps(log_obj)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("gateway")
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger.handlers = [handler]
logger.propagate = False

# Initialize FastAPI App
_EXPOSE_DOCS = settings.APP_ENV.lower() in {"demo", "development"}
app = FastAPI(
    title="Enterprise A2A Cloud Run Interceptor Gateway",
    version=settings.SERVICE_VERSION,
    description="Enterprise A2A policy gateway with security controls and a non-validated regulated-workflow prototype.",
    lifespan=lifespan,
    docs_url="/docs" if _EXPOSE_DOCS else None,
    redoc_url="/redoc" if _EXPOSE_DOCS else None,
    openapi_url="/openapi.json" if _EXPOSE_DOCS else None,
)

# Cross-origin browser access is deny-by-default outside explicit local/demo origins.
_configured_cors_origins = [
    origin.strip()
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
_local_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8090",
    "http://127.0.0.1:8090",
] if settings.APP_ENV.lower() in {"demo", "development"} else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_local_cors_origins + _configured_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "A2A-Version", "A2A-Extensions"],
)

from .rate_limiter import RateLimiterMiddleware
app.add_middleware(RateLimiterMiddleware)

# Standards-facing A2A v1.0 JSON-RPC surface and Agent Card.
app.include_router(a2a_v1_router)


def require_lab_mode() -> None:
    """Hide experimental mutation/control APIs unless explicitly enabled."""
    if not settings.ENABLE_LAB_ENDPOINTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    if settings.APP_ENV.lower() in {"staging", "production"}:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Background Worker for Out-of-Band Push Notification
async def dispatch_push_notification(push_url: str, task_id: str, decision: str, study_id: str, cohort: str):
    """Deliver terminal task completion webhook to Gemini Enterprise."""
    safe, reason = is_safe_webhook_url(push_url)
    if not safe:
        logger.error(
            f"SSRF Guard Blocked push notification to {push_url}: {reason}",
            extra={"extra_data": {"taskId": task_id, "pushUrl": push_url, "reason": reason}},
        )
        return

    try:
        now_utc = datetime.now(timezone.utc).isoformat()
        payload = {
            "jsonrpc": "2.0",
            "method": "a2a.tasks.notify",
            "params": {
                "taskId": task_id,
                "status": "COMPLETED",
                "output": {
                    "studyId": study_id,
                    "cohort": cohort,
                    "decision": decision,
                    "signedOffAt": now_utc,
                    "auditedBy": "authenticated gateway reviewer",
                    "controlEvidence": "cryptographic approval token verified; regulatory validation not asserted",
                },
            },
            "id": str(uuid.uuid4()),
        }
        headers = {"Content-Type": "application/json", "X-Enterprise-Policy-Gateway": "Controls-Verified"}
        client = getattr(app.state, "http_client", None)
        close_client = False
        if client is None or client.is_closed:
            client = httpx.AsyncClient(timeout=15.0)
            close_client = True
        try:
            resp = await client.post(push_url, json=payload, headers=headers)
            logger.info(
                f"Push notification delivered to {push_url}. Status: {resp.status_code}",
                extra={"extra_data": {"taskId": task_id, "pushStatus": resp.status_code}},
            )
        finally:
            if close_client:
                await client.aclose()
    except Exception as exc:
        logger.error(
            f"Failed delivering push notification to {push_url}: {str(exc)}",
            extra={"extra_data": {"taskId": task_id, "error": str(exc)}},
        )


# Health Check
@app.get("/")
@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Cloud Run health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "environment": settings.APP_ENV,
        "version": settings.SERVICE_VERSION,
        "securityMode": "explicit-dev-bypass" if settings.ALLOW_DEV_AUTH else "oidc-required",
        "regulatedUse": "prototype-not-validated",
    }


# Sovereign Biopharma Swarm Registration & 21 CFR Part 11 Validation Models
class SwarmRegistrationPayload(BaseModel):
    client_name: str
    organization: str
    gateway_target: Optional[str] = None
    security_scheme: str = "HMAC-SHA256"
    compliance_frameworks: list[str] = ["21_CFR_Part_11", "Annex_11"]
    signature_manifestation: Optional[Dict[str, Any]] = None


class SignedEnvelope(BaseModel):
    payload: Dict[str, Any]
    signature: str
    document_data: Any
    max_age_hours: int = Field(default=72, ge=1, le=720)


SWARM_CLIENTS_REGISTRY: Dict[str, Any] = {}
SIGNATURE_RECEIPTS_REGISTRY: Dict[str, Any] = {}


@app.post("/api/v1/register")
async def register_swarm_client(
    payload: SwarmRegistrationPayload,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Register sovereign biopharma agent swarm for stateless 21 CFR Part 11 communication."""
    require_lab_mode()
    del auth_claims
    client_id = f"swarm-{uuid.uuid4().hex[:12]}"
    reg_id = f"reg-21cfr11-{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    supported_meanings = [
        "ProtocolApproval",
        "CohortValidation",
        "SafetyReview",
        "SystemAudit",
        "DoseTitrationApproval",
        "DeviationJustification",
    ]
    if payload.signature_manifestation and "supported_meanings" in payload.signature_manifestation:
        supported_meanings = payload.signature_manifestation["supported_meanings"]

    record = {
        "status": "REGISTERED",
        "client_id": client_id,
        "client_name": payload.client_name,
        "organization": payload.organization,
        "registration_id": reg_id,
        "registered_at": now_iso,
        "gateway_target": payload.gateway_target or "https://a2a-gateway-638420508320.us-central1.run.app",
        "security_scheme": payload.security_scheme,
        "compliance_status": "CONTROL_PROTOTYPE_NOT_VALIDATED",
        "supported_meanings": supported_meanings,
        "verification_endpoint": "/api/v1/verify-signature",
        "uri": f"/api/v1/swarms/{client_id}",
        "_links": {
            "self": {"href": f"/api/v1/swarms/{client_id}"},
            "registration": {"href": f"/api/v1/registrations/{reg_id}"},
            "verify": {"href": "/api/v1/verify-signature"},
        },
        "message": "Swarm registration created for a Part 11-aligned control prototype; customer validation is required."
    }
    SWARM_CLIENTS_REGISTRY[client_id] = record
    SWARM_CLIENTS_REGISTRY[reg_id] = record
    return record


@app.get("/api/v1/swarms/{client_id}")
async def get_swarm_client(
    client_id: str,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Retrieve an existing swarm registration; unknown IDs never fail open."""
    require_lab_mode()
    del auth_claims
    if client_id not in SWARM_CLIENTS_REGISTRY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Swarm client not found")
    return SWARM_CLIENTS_REGISTRY[client_id]


@app.get("/api/v1/registrations/{registration_id}")
async def get_swarm_registration(
    registration_id: str,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Retrieve an existing registration; unknown IDs return 404."""
    require_lab_mode()
    del auth_claims
    if registration_id not in SWARM_CLIENTS_REGISTRY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
    return SWARM_CLIENTS_REGISTRY[registration_id]


@app.post("/api/v1/create-signature")
async def create_swarm_signature(
    request: Request,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Create identity-bound cryptographic control evidence.

    Signer identity is derived from verified OIDC claims, never caller input.
    This is a technical control prototype, not a regulatory certification.
    """
    require_lab_mode()
    data = await request.json()
    document_id = str(data.get("document_id") or "").strip()
    if "document_data" not in data or not document_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="document_id and document_data are required",
        )
    if auth_claims.get("email_verified") is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verified signer identity is required")

    signer_id = str(auth_claims.get("sub") or "").strip()
    signer_name = str(auth_claims.get("name") or auth_claims.get("email") or signer_id).strip()
    if not signer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OIDC subject is required")

    signer = CFRPart11Signer()
    try:
        envelope = signer.create_signature_payload(
            agent_id=signer_id,
            agent_name=signer_name,
            meaning=data.get("meaning", "ProtocolApproval"),
            document_id=document_id,
            document_data=data["document_data"],
            extra_metadata={
                "identity_source": "google_oidc",
                "validation_status": "prototype-not-validated",
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return envelope


@app.post("/api/v1/verify-signature")
async def verify_swarm_signature(
    envelope: SignedEnvelope,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Verify cryptographic integrity, record linking and signature age."""
    require_lab_mode()
    del auth_claims
    signer = CFRPart11Signer()
    is_valid, reason = signer.verify_signature(
        {"payload": envelope.payload, "signature": envelope.signature},
        document_data=envelope.document_data,
        max_age_hours=envelope.max_age_hours,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Electronic-signature verification failed: {reason}",
        )

    receipt_id = f"sig-rec-{hashlib.sha256(envelope.signature.encode()).hexdigest()[:16]}"
    receipt = {
        "valid": True,
        "receipt_id": receipt_id,
        "signer_id": envelope.payload.get("signer_id"),
        "signer_name": envelope.payload.get("signer_name"),
        "meaning": envelope.payload.get("meaning"),
        "document_id": envelope.payload.get("document_id"),
        "document_hash": envelope.payload.get("document_hash"),
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "control_standard": "PART_11_ALIGNED_TECHNICAL_CONTROLS",
        "validation_status": "PROTOTYPE_NOT_VALIDATED",
        "audit_status": "CRYPTOGRAPHIC_LINK_VERIFIED",
        "uri": f"/api/v1/signatures/{receipt_id}",
        "_links": {"self": {"href": f"/api/v1/signatures/{receipt_id}"}},
        "message": reason,
    }
    SIGNATURE_RECEIPTS_REGISTRY[receipt_id] = receipt
    return receipt


@app.get("/api/v1/signatures/{receipt_id}")
async def get_signature_receipt(
    receipt_id: str,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    require_lab_mode()
    del auth_claims
    if receipt_id not in SIGNATURE_RECEIPTS_REGISTRY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature receipt not found")
    return SIGNATURE_RECEIPTS_REGISTRY[receipt_id]


@app.get("/api/v1/dossiers/{dossier_id}")
async def get_fda_dossier_resource(
    dossier_id: str,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Return a demo dossier template only when lab endpoints are explicitly enabled."""
    require_lab_mode()
    del auth_claims
    return {
        "dossier_id": dossier_id,
        "status": "DEMO_TEMPLATE",
        "validation_status": "NOT_VALIDATED",
        "compliance_mapping": "21_CFR_PART_11_REFERENCE_ONLY",
        "uri": f"/api/v1/dossiers/{dossier_id}",
    }


# Task Execution & Interception
@app.post("/a2a/tasks")
async def handle_task_dispatch(
    request: Request,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Receive A2A JSON-RPC 2.0 task request from Gemini Enterprise.

    Strips proprietary Google ADK envelope metadata, then forwards to downstream
    or operates in standalone mock mode.
    """
    raw_body = await request.body()
    try:
        incoming_json = json.loads(raw_body) if raw_body else {}
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: Invalid JSON body ({str(exc)})",
                },
                "id": None,
            },
        )

    if not isinstance(incoming_json, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Top-level payload must be a JSON object.",
                },
                "id": None,
            },
        )

    # JSON-RPC 2.0 Structural Conformance
    jsonrpc_ver = incoming_json.get("jsonrpc")
    if jsonrpc_ver is not None and jsonrpc_ver != "2.0":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": f"Invalid Request: Unsupported JSON-RPC version '{jsonrpc_ver}'. Protocol requires '2.0'.",
                },
                "id": incoming_json.get("id"),
            },
        )

    method = incoming_json.get("method")
    if jsonrpc_ver == "2.0" and not method:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Missing or empty 'method' parameter in JSON-RPC request.",
                },
                "id": incoming_json.get("id"),
            },
        )

    params = incoming_json.get("params")
    if params is not None and not isinstance(params, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params: 'params' must be a JSON object.",
                },
                "id": incoming_json.get("id"),
            },
        )

    if method in ("a2a.tasks.send", "tasks.send") and isinstance(params, dict):
        if not any(k in params for k in ("taskId", "studyId", "input", "task", "pushUrl")):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": "Invalid params: 'a2a.tasks.send' requires at least one of 'taskId', 'studyId', or 'input'.",
                    },
                    "id": incoming_json.get("id"),
                },
            )

    # 1. Sanitize incoming payload (Drop adk_metadata, _adk, __adk*, ge_context, etc.)
    cleaned_payload = sanitize_a2a_envelope(incoming_json)
    cleaned_headers = sanitize_headers(dict(request.headers))

    logger.info(
        "Sanitized incoming A2A task payload",
        extra={"extra_data": {"user": auth_claims.get("email"), "sanitizedKeys": list(cleaned_payload.keys())}},
    )

    # 2. Check if downstream agent is configured (Reverse Proxy Mode)
    if settings.DOWNSTREAM_AGENT_URL:
        target_url = settings.DOWNSTREAM_AGENT_URL.rstrip("/") + "/a2a/tasks"
        logger.info(f"Forwarding sanitized payload to downstream agent: {target_url}")

        client = getattr(app.state, "http_client", None)
        close_client = False
        if client is None or client.is_closed:
            client = httpx.AsyncClient(timeout=settings.DOWNSTREAM_TIMEOUT_SECONDS)
            close_client = True

        downstream_headers = dict(cleaned_headers)
        if settings.DOWNSTREAM_ID_TOKEN_AUDIENCE:
            try:
                destination_token = await asyncio.to_thread(
                    mint_downstream_id_token,
                    settings.DOWNSTREAM_ID_TOKEN_AUDIENCE,
                )
            except Exception as exc:
                logger.error("Unable to mint downstream workload identity token")
                if close_client:
                    await client.aclose()
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "jsonrpc": "2.0",
                        "id": cleaned_payload.get("id"),
                        "error": {
                            "code": -32006,
                            "message": "Downstream authentication is unavailable",
                        },
                    },
                )
            downstream_headers["Authorization"] = f"Bearer {destination_token}"

        req = client.build_request(
            method="POST",
            url=target_url,
            headers=downstream_headers,
            json=cleaned_payload,
        )

        response = await client.send(req, stream=True)

        # Check for SSE streaming response
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            async def event_generator():
                buffer = b""
                try:
                    async for chunk in response.aiter_raw():
                        if await request.is_disconnected():
                            logger.info("Client disconnected during SSE stream; stopping upstream consumption.")
                            break
                        buffer += chunk
                        buffer = buffer.replace(b"\r\n", b"\n")
                        while b"\n\n" in buffer:
                            raw_event, buffer = buffer.split(b"\n\n", 1)
                            if raw_event.strip():
                                yield sanitize_sse_event(raw_event + b"\n\n")
                    if buffer.strip():
                        yield sanitize_sse_event(buffer + b"\n\n")
                except Exception as exc:
                    logger.error(f"Upstream SSE event blocked by gateway policy: {exc}")
                    safe_error = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": "Upstream stream blocked by gateway policy"},
                    }
                    yield ("data: " + json.dumps(safe_error) + "\n\n").encode("utf-8")
                finally:
                    await response.aclose()
                    if close_client:
                        await client.aclose()

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            resp_bytes = await response.aread()
            await response.aclose()
            if close_client:
                await client.aclose()
            try:
                resp_json = json.loads(resp_bytes)
                sanitized_resp = sanitize_payload(resp_json)
                return JSONResponse(content=sanitized_resp, status_code=response.status_code)
            except Exception:
                logger.error("Blocked non-JSON downstream response on policy gateway")
                return JSONResponse(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    content={
                        "jsonrpc": "2.0",
                        "id": cleaned_payload.get("id"),
                        "error": {
                            "code": -32006,
                            "message": "Downstream returned a response that cannot be safely normalized",
                        },
                    },
                )

    # 3. Standalone Mode: Generate HITL Input Required Response with Sealed A2UI Artifact
    params = cleaned_payload.get("params", {})
    task_id = params.get("taskId") or f"task-{uuid.uuid4().hex[:8]}"
    study_id = params.get("studyId") or params.get("input", {}).get("studyId") or "MK-3475-001"
    cohort = params.get("cohort") or params.get("input", {}).get("cohort") or "Cohort-B"
    push_url = params.get("pushUrl") or params.get("pushNotificationConfig", {}).get("url")

    # SSRF Guard: Validate push_url if provided
    if push_url:
        safe, reason = is_safe_webhook_url(push_url)
        if not safe:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": f"Invalid params: Insecure or prohibited pushUrl (SSRF Guard Active): {reason}",
                    },
                    "id": cleaned_payload.get("id"),
                },
            )

    # Generate the dual-dialect surface with sealed state tokens
    surface = build_clinical_review_surface(
        task_id=task_id,
        study_id=study_id,
        cohort=cohort,
        push_url=push_url,
        protocol_version="v4.2",
        variance_pct=2.14,
        approver_subject=auth_claims.get("sub"),
    )

    response_body = {
        "jsonrpc": "2.0",
        "id": cleaned_payload.get("id", str(uuid.uuid4())),
        "result": {
            "taskId": task_id,
            "status": "INPUT_REQUIRED",
            "message": f"Clinical dossier review required for Study {study_id} ({cohort}).",
            "artifact": {
                "type": "a2ui_surface",
                "a2ui": surface["a2ui"],
                "googleCardV2": surface["googleCardV2"],
            },
        },
    }

    return JSONResponse(content=response_body, status_code=200)


# UI Action Callback Endpoint
@app.post("/a2a/ui/action")
async def handle_ui_action(
    request: Request,
    background_tasks: BackgroundTasks,
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    """Process user interactive action from A2UI or Google Card buttons.

    Unpacks cryptographically sealed state token, verifies 48-hour signature,
    and asynchronously notifies GE via push webhook.
    """
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body) if raw_body else {}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {str(exc)}")

    cleaned_payload = sanitize_payload(payload)

    # Extract state token from various possible locations (A2UI direct, params.data, action parameters)
    state_token = None
    params = cleaned_payload.get("params", {})

    if isinstance(params, dict):
        state_token = (
            params.get("stateToken")
            or params.get("data", {}).get("stateToken")
            or cleaned_payload.get("stateToken")
        )

    # Check Google Card action parameters format
    if not state_token:
        action_params = (
            cleaned_payload.get("action", {}).get("parameters", [])
            or params.get("action", {}).get("parameters", [])
        )
        if isinstance(action_params, list):
            for p in action_params:
                if isinstance(p, dict) and p.get("key") == "stateToken":
                    state_token = p.get("value")
                    break

    if not state_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required stateToken in action payload",
        )

    # Extract form inputs & clinical justifications if provided in A2UI action
    form_inputs = (
        cleaned_payload.get("formInputs")
        or params.get("formInputs")
        or cleaned_payload.get("inputs")
        or {}
    )
    justification = (
        cleaned_payload.get("justification")
        or params.get("justification")
        or (form_inputs.get("justificationRationale") if isinstance(form_inputs, dict) else "")
        or ""
    )

    # Atomically verify signature and consume JTI nonce statelessly (guards against replay attacks)
    state_claims = consume_state_token(state_token)

    bound_subject = state_claims.get("approverSub")
    current_subject = auth_claims.get("sub")
    if bound_subject and bound_subject != current_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approval token is bound to a different authenticated subject",
        )
    if not bound_subject and settings.APP_ENV.lower() in {"staging", "production"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unbound legacy approval tokens are not accepted in staging/production",
        )

    task_id = state_claims.get("taskId", "unknown-task")
    study_id = state_claims.get("studyId", "unknown-study")
    cohort = state_claims.get("cohort", "unknown-cohort")
    decision = state_claims.get("decision", "APPROVED")
    push_url = state_claims.get("pushUrl")

    logger.info(
        f"Stateless state token validated successfully for Task {task_id}: Decision={decision}",
        extra={"extra_data": {"taskId": task_id, "studyId": study_id, "decision": decision}},
    )

    # If pushUrl was embedded in the sealed token, schedule asynchronous webhook notification
    if push_url:
        background_tasks.add_task(
            dispatch_push_notification,
            push_url=push_url,
            task_id=task_id,
            decision=decision,
            study_id=study_id,
            cohort=cohort,
        )

    now_utc = datetime.now(timezone.utc).isoformat()

    # Return finalized task response
    return {
        "jsonrpc": "2.0",
        "id": cleaned_payload.get("id", str(uuid.uuid4())),
        "result": {
            "taskId": task_id,
            "status": "COMPLETED",
            "decision": decision,
            "studyId": study_id,
            "cohort": cohort,
            "stateVerified": True,
            "jti": state_claims.get("jti"),
            "formInputs": form_inputs,
            "justification": justification,
            "audit": {
                "tokenIssuer": state_claims.get("iss"),
                "tokenIssuedAt": state_claims.get("iat"),
                "tokenExpiresAt": state_claims.get("exp"),
                "jtiNonce": state_claims.get("jti"),
                "verifiedAt": now_utc,
                "controlEvidenceGenerated": True,
                "validationStatus": "prototype-not-validated",
                "authenticatedSubject": current_subject,
                "electronicSignatureControl": {
                    "meaning": "Authenticated user executed the bound review action.",
                    "timestamp": now_utc,
                    "part11Alignment": "technical-controls-only",
                },
            },
        },
    }
