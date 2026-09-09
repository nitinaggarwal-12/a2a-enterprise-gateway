"""A2A Protocol v1.0 JSON-RPC compatibility surface.

The legacy clinical demo endpoints remain available separately. This module
implements the standards-facing discovery and core JSON-RPC operations using
A2A v1.0 field names and version negotiation.
"""

import asyncio
from collections import OrderedDict
from datetime import datetime, timezone
import hashlib
import json
import threading
import uuid
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .a2ui_builder import build_clinical_review_surface
from .config import settings
from .sanitizer import sanitize_a2a_envelope, sanitize_payload
from .security import mint_downstream_id_token, verify_google_oidc


router = APIRouter()
SUPPORTED_PROTOCOL_VERSION = "1.0"
MAX_DEMO_TASKS = 1000
_TASKS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_TASK_LOCK = threading.Lock()

ERROR_TASK_NOT_FOUND = -32001
ERROR_TASK_NOT_CANCELABLE = -32002
ERROR_PUSH_NOT_SUPPORTED = -32003
ERROR_UNSUPPORTED_OPERATION = -32004
ERROR_VERSION_NOT_SUPPORTED = -32009


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _jsonrpc_error(request_id: Any, code: int, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        },
    )


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def build_agent_card(request: Request) -> Dict[str, Any]:
    base = _base_url(request)
    return {
        "name": "Enterprise A2A Policy Gateway",
        "description": (
            "A2A v1.0 JSON-RPC gateway for policy-controlled agent interoperability. "
            "Regulated-workflow controls are provided as enterprise extensions and "
            "must be validated in the customer's operating environment."
        ),
        "supportedInterfaces": [
            {
                "url": f"{base}/a2a/v1",
                "protocolBinding": "JSONRPC",
                "protocolVersion": SUPPORTED_PROTOCOL_VERSION,
            }
        ],
        "provider": {
            "organization": "A2A Enterprise Gateway Project",
            "url": base,
        },
        "version": settings.SERVICE_VERSION,
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "extendedAgentCard": False,
            "extensions": [
                {
                    "uri": f"{base}/extensions/policy-gateway/v1",
                    "description": "Enterprise policy, sanitization and HITL metadata extension.",
                    "required": False,
                }
            ],
        },
        "securitySchemes": {
            "googleOidc": {
                "openIdConnectSecurityScheme": {
                    "openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration",
                    "description": "Google OIDC bearer token validated for the configured gateway audience.",
                }
            }
        },
        "securityRequirements": [
            {"schemes": {"googleOidc": {"list": ["openid", "email"]}}}
        ],
        "defaultInputModes": ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {
                "id": "policy-controlled-task-routing",
                "name": "Policy-controlled A2A task routing",
                "description": (
                    "Accepts A2A messages, applies gateway sanitization and policy controls, "
                    "and routes to a configured downstream agent or a non-production demo task."
                ),
                "tags": ["a2a", "gateway", "policy", "security", "hitl"],
                "inputModes": ["application/json", "text/plain"],
                "outputModes": ["application/json"],
            }
        ],
    }


@router.get("/.well-known/agent-card.json")
async def get_agent_card(request: Request):
    card = build_agent_card(request)
    etag = hashlib.sha256(json.dumps(card, sort_keys=True).encode("utf-8")).hexdigest()
    return JSONResponse(
        content=card,
        headers={
            "Cache-Control": "public, max-age=300",
            "ETag": f'"{etag}"',
        },
    )


@router.get("/.well-known/agent.json")
async def legacy_agent_card_redirect():
    """Backward-compatible redirect; v1.0 discovery uses agent-card.json."""
    return RedirectResponse(
        url="/.well-known/agent-card.json",
        status_code=308,
        headers={"Deprecation": "true"},
    )


def _version_or_error(request_id: Any, version: Optional[str]) -> Optional[JSONResponse]:
    requested = version or "0.3"
    if requested != SUPPORTED_PROTOCOL_VERSION:
        return _jsonrpc_error(
            request_id,
            ERROR_VERSION_NOT_SUPPORTED,
            f"A2A protocol version '{requested}' is not supported by this interface; use 1.0",
        )
    return None


def _store_task(task: Dict[str, Any]) -> None:
    with _TASK_LOCK:
        _TASKS[task["id"]] = task
        _TASKS.move_to_end(task["id"])
        while len(_TASKS) > MAX_DEMO_TASKS:
            _TASKS.popitem(last=False)


def _get_task(task_id: str) -> Optional[Dict[str, Any]]:
    with _TASK_LOCK:
        task = _TASKS.get(task_id)
        return json.loads(json.dumps(task)) if task else None


async def _proxy_to_downstream(payload: Dict[str, Any], version: str, extensions: Optional[str]) -> JSONResponse:
    target = settings.DOWNSTREAM_AGENT_URL.rstrip("/") + "/a2a/v1"
    headers = {
        "Content-Type": "application/json",
        "A2A-Version": version,
    }
    if extensions:
        headers["A2A-Extensions"] = extensions
    if settings.DOWNSTREAM_ID_TOKEN_AUDIENCE:
        try:
            token = await asyncio.to_thread(
                mint_downstream_id_token,
                settings.DOWNSTREAM_ID_TOKEN_AUDIENCE,
            )
        except Exception:
            return _jsonrpc_error(
                payload.get("id"),
                -32006,
                "Downstream authentication is unavailable",
                503,
            )
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=settings.DOWNSTREAM_TIMEOUT_SECONDS) as client:
        response = await client.post(target, json=sanitize_a2a_envelope(payload), headers=headers)
    try:
        body = sanitize_payload(response.json())
        return JSONResponse(content=body, status_code=response.status_code)
    except Exception:
        return _jsonrpc_error(payload.get("id"), -32006, "Downstream returned an invalid A2A response", 502)


def _validate_message(message: Any) -> Optional[str]:
    if not isinstance(message, dict):
        return "SendMessage requires params.message"
    if not message.get("messageId"):
        return "message.messageId is required"
    if message.get("role") not in {"ROLE_USER", "ROLE_AGENT"}:
        return "message.role must be ROLE_USER or ROLE_AGENT"
    parts = message.get("parts")
    if not isinstance(parts, list) or not parts:
        return "message.parts must contain at least one Part"
    for part in parts:
        if not isinstance(part, dict):
            return "each message Part must be an object"
        one_of = sum(key in part for key in ("text", "raw", "url", "data"))
        if one_of != 1:
            return "each message Part must contain exactly one of text, raw, url, data"
    return None


def _demo_send_message(params: Dict[str, Any], approver_subject: Optional[str]) -> Dict[str, Any]:
    message = sanitize_payload(params["message"])
    existing_task_id = message.get("taskId")
    if existing_task_id:
        existing = _get_task(existing_task_id)
        if not existing:
            raise KeyError(existing_task_id)
        if message.get("contextId") and message["contextId"] != existing.get("contextId"):
            raise ValueError("message contextId does not match referenced task")
        existing.setdefault("history", []).append(message)
        existing["status"] = {
            "state": "TASK_STATE_WORKING",
            "timestamp": _utcnow(),
        }
        _store_task(existing)
        return existing

    task_id = str(uuid.uuid4())
    context_id = message.get("contextId") or str(uuid.uuid4())

    metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
    study_id = str(metadata.get("studyId", "DEMO-STUDY"))
    cohort = str(metadata.get("cohort", "DEMO-COHORT"))
    surface = build_clinical_review_surface(
        task_id=task_id,
        study_id=study_id,
        cohort=cohort,
        push_url=None,
        variance_pct=0.0,
        approver_subject=approver_subject,
    )

    status_message = {
        "messageId": str(uuid.uuid4()),
        "contextId": context_id,
        "taskId": task_id,
        "role": "ROLE_AGENT",
        "parts": [{"text": "Human review is required before this demo task can continue."}],
    }
    task = {
        "id": task_id,
        "contextId": context_id,
        "status": {
            "state": "TASK_STATE_INPUT_REQUIRED",
            "message": status_message,
            "timestamp": _utcnow(),
        },
        "artifacts": [
            {
                "artifactId": str(uuid.uuid4()),
                "name": "human-review-surface",
                "description": "Non-production A2UI/HITL review payload.",
                "parts": [
                    {
                        "data": {
                            "a2ui": surface["a2ui"],
                            "googleCardV2": surface["googleCardV2"],
                            "controlStatus": "prototype-not-validated",
                        },
                        "mediaType": "application/json",
                    }
                ],
            }
        ],
        "history": [message],
        "metadata": {
            "gatewayMode": "demo",
            "persistence": "ephemeral",
            "regulatedUse": "not-validated",
        },
    }
    _store_task(task)
    return task


@router.post("/a2a/v1")
async def a2a_jsonrpc_v1(
    request: Request,
    a2a_version: Optional[str] = Header(None, alias="A2A-Version"),
    a2a_extensions: Optional[str] = Header(None, alias="A2A-Extensions"),
    auth_claims: Dict[str, Any] = Depends(verify_google_oidc),
):
    try:
        body = await request.json()
    except Exception:
        return _jsonrpc_error(None, -32700, "Invalid JSON payload")

    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        return _jsonrpc_error(body.get("id") if isinstance(body, dict) else None, -32600, "Request payload validation error")

    request_id = body.get("id")
    version_error = _version_or_error(request_id, a2a_version)
    if version_error:
        return version_error

    method = body.get("method")
    params = body.get("params") or {}
    if not isinstance(params, dict):
        return _jsonrpc_error(request_id, -32602, "Invalid parameters")

    # A configured production gateway delegates execution to its downstream A2A agent.
    if settings.DOWNSTREAM_AGENT_URL:
        return await _proxy_to_downstream(body, SUPPORTED_PROTOCOL_VERSION, a2a_extensions)

    # Never pretend an ephemeral demo task registry is production persistence.
    if settings.APP_ENV.lower() in {"staging", "production"}:
        return _jsonrpc_error(
            request_id,
            ERROR_UNSUPPORTED_OPERATION,
            "No durable downstream A2A agent is configured for this production gateway",
            503,
        )

    if method == "SendMessage":
        validation_error = _validate_message(params.get("message"))
        if validation_error:
            return _jsonrpc_error(request_id, -32602, validation_error)
        try:
            task = _demo_send_message(params, auth_claims.get("sub"))
        except KeyError:
            return _jsonrpc_error(request_id, ERROR_TASK_NOT_FOUND, "Referenced task was not found", 404)
        except ValueError as exc:
            return _jsonrpc_error(request_id, -32602, str(exc))
        return JSONResponse(content={"jsonrpc": "2.0", "id": request_id, "result": {"task": task}})

    if method == "GetTask":
        task_id = params.get("id")
        task = _get_task(str(task_id)) if task_id else None
        if not task:
            return _jsonrpc_error(request_id, ERROR_TASK_NOT_FOUND, "Task not found", 404)
        history_length = params.get("historyLength")
        if isinstance(history_length, int) and history_length >= 0 and "history" in task:
            task["history"] = task["history"][-history_length:] if history_length else []
        return JSONResponse(content={"jsonrpc": "2.0", "id": request_id, "result": task})

    if method == "ListTasks":
        page_size = params.get("pageSize", 50)
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            return _jsonrpc_error(request_id, -32602, "pageSize must be between 1 and 100")
        with _TASK_LOCK:
            tasks = list(_TASKS.values())
        context_id = params.get("contextId")
        state = params.get("status")
        if context_id:
            tasks = [task for task in tasks if task.get("contextId") == context_id]
        if state:
            tasks = [task for task in tasks if task.get("status", {}).get("state") == state]
        selected = json.loads(json.dumps(tasks[:page_size]))
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tasks": selected,
                "nextPageToken": "",
                "pageSize": page_size,
                "totalSize": len(tasks),
            },
        })

    if method == "CancelTask":
        task_id = str(params.get("id") or "")
        task = _get_task(task_id)
        if not task:
            return _jsonrpc_error(request_id, ERROR_TASK_NOT_FOUND, "Task not found", 404)
        terminal = {
            "TASK_STATE_COMPLETED",
            "TASK_STATE_FAILED",
            "TASK_STATE_CANCELED",
            "TASK_STATE_REJECTED",
        }
        if task.get("status", {}).get("state") in terminal:
            return _jsonrpc_error(request_id, ERROR_TASK_NOT_CANCELABLE, "Task is already in a terminal state")
        task["status"] = {"state": "TASK_STATE_CANCELED", "timestamp": _utcnow()}
        _store_task(task)
        return JSONResponse(content={"jsonrpc": "2.0", "id": request_id, "result": task})

    if method in {"SendStreamingMessage", "SubscribeToTask"}:
        return _jsonrpc_error(request_id, ERROR_UNSUPPORTED_OPERATION, "Streaming is not advertised by this gateway")

    if method in {
        "CreateTaskPushNotificationConfig",
        "GetTaskPushNotificationConfig",
        "ListTaskPushNotificationConfigs",
        "DeleteTaskPushNotificationConfig",
    }:
        return _jsonrpc_error(request_id, ERROR_PUSH_NOT_SUPPORTED, "Push notifications are not advertised by this gateway")

    if method == "GetExtendedAgentCard":
        return _jsonrpc_error(request_id, ERROR_UNSUPPORTED_OPERATION, "Extended Agent Card is not advertised by this gateway")

    return _jsonrpc_error(request_id, -32601, "Method not found")
