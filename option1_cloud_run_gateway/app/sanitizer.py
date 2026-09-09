"""Policy sanitization for A2A payloads, headers, and SSE events.

This module is intentionally fail-closed for transport metadata and obvious
credential material. It is not a substitute for tenant-specific DLP policies,
but it prevents the gateway from forwarding known orchestration internals and
credential-bearing fields by default.
"""

import json
import re
from typing import Any, Dict, List, Set, Union


PROHIBITED_KEYS: Set[str] = {
    "adk_metadata",
    "_adk",
    "ge_context",
    "agent_metadata",
    "adk_internal_context",
    "__internal_trace__",
    "system_override",
}

SENSITIVE_KEY_TOKENS = (
    "password",
    "passwd",
    "secret",
    "access_token",
    "refresh_token",
    "id_token",
    "api_key",
    "apikey",
    "private_key",
    "client_secret",
    "credential",
)

STRIP_HEADER_PREFIXES = (
    "x-google-adk",
    "x-goog-",
    "x-adk",
)

STRIP_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "host",
    "content-length",
    "connection",
    "keep-alive",
    "proxy-connection",
    "transfer-encoding",
    "te",
    "trailer",
    "upgrade",
    "forwarded",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
}

_TEXT_SECRET_PATTERNS = (
    re.compile(r"(?i)bearer\\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"(?i)(api[_ -]?key|client[_ -]?secret|password)\\s*[:=]\\s*[^\\s,;]{6,}"),
)


def is_prohibited_key(key: str) -> bool:
    """Return True for internal metadata and obvious credential-bearing keys."""
    if not isinstance(key, str):
        return False
    lower_key = key.lower().strip()
    if lower_key in PROHIBITED_KEYS:
        return True
    if lower_key.startswith("__adk") or lower_key.startswith("_adk_"):
        return True
    normalized = lower_key.replace("-", "_")
    return any(token in normalized for token in SENSITIVE_KEY_TOKENS)


def _sanitize_text(value: str) -> str:
    cleaned = value
    for pattern in _TEXT_SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED_BY_GATEWAY]", cleaned)
    return cleaned


def sanitize_payload(obj: Any) -> Any:
    """Recursively remove prohibited metadata and credential-bearing fields."""
    if isinstance(obj, dict):
        cleaned_dict: Dict[str, Any] = {}
        for key, value in obj.items():
            if is_prohibited_key(str(key)):
                continue
            cleaned_dict[key] = sanitize_payload(value)
        return cleaned_dict
    if isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(sanitize_payload(item) for item in obj)
    if isinstance(obj, set):
        return {sanitize_payload(item) for item in obj}
    if isinstance(obj, str):
        return _sanitize_text(obj)
    return obj


def sanitize_a2a_envelope(obj: Any) -> Dict[str, Any]:
    """Sanitize an A2A/JSON-RPC envelope and drop undeclared top-level wrappers.

    Only protocol envelope fields are forwarded. Extension data belongs under
    metadata/params rather than as arbitrary top-level vendor fields.
    """
    if not isinstance(obj, dict):
        raise ValueError("A2A payload must be a JSON object")

    allowed_top_level = {"jsonrpc", "method", "params", "id", "metadata"}
    cleaned = sanitize_payload(obj)
    return {key: value for key, value in cleaned.items() if key in allowed_top_level}


def sanitize_headers(headers: Union[Dict[str, str], List[tuple]]) -> Dict[str, str]:
    """Prepare caller headers for downstream forwarding.

    Caller credentials and proxy-derived identity headers are never forwarded;
    downstream credentials must be minted explicitly for the destination.
    """
    cleaned: Dict[str, str] = {}
    items = headers.items() if isinstance(headers, dict) else headers

    for key, value in items:
        lower_key = str(key).lower().strip()
        if any(lower_key.startswith(prefix) for prefix in STRIP_HEADER_PREFIXES):
            continue
        if lower_key in STRIP_HEADERS:
            continue
        cleaned[str(key)] = str(value)

    return cleaned


def sanitize_sse_event(event: bytes) -> bytes:
    """Sanitize one complete Server-Sent Event.

    A2A streaming data frames are expected to carry JSON. Non-JSON data frames
    are rejected rather than bypassing the policy boundary.
    """
    text = event.decode("utf-8")
    output: List[str] = []
    for line in text.splitlines():
        if not line.startswith("data:"):
            output.append(line)
            continue

        raw_data = line[5:].lstrip()
        if not raw_data:
            output.append("data:")
            continue
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise ValueError("Non-JSON SSE data frame rejected by gateway policy") from exc

        sanitized = sanitize_payload(payload)
        output.append("data: " + json.dumps(sanitized, separators=(",", ":"), ensure_ascii=False))

    return ("\\n".join(output) + "\\n\\n").encode("utf-8")
