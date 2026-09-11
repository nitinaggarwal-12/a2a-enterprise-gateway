"""Sanitizer module for stripping proprietary Google ADK metadata and envelope headers.

Enterprise GxP validation parsers (21 CFR Part 11 strict schema compliance) require
complete elimination of undeclared metadata fields and vendor-specific envelopes.
"""

import json
from typing import Any, Dict, List, Set, Union


# Prohibited metadata keys exact match set (including orchestrator traces, prompt overrides, and leaked credentials)
PROHIBITED_KEYS: Set[str] = {
    "adk_metadata",
    "_adk",
    "ge_context",
    "agent_metadata",
    "__internal_trace__",
    "adk_internal_context",
    "prompt_injection_flag",
    "prompt_injection_flags",
    "raw_system_prompt",
    "__system_instructions__",
    "system_override",
    "leaked_jwt_secret",
    "system_prompt_raw",
    "internal_context",
    "agent_credentials",
    "internal_auth",
    "adk_debug",
    "ge_token",
    "leaked_secret",
    "internal_trace",
    "system_prompt",
}

# Key prefixes that indicate orchestrator envelopes or internal diagnostics
PROHIBITED_KEY_PREFIXES = (
    "__adk",
    "__internal",
    "_adk",
    "x_adk",
    "x-adk",
    "ge_",
)

# Header prefixes to strip before reverse-proxying downstream
STRIP_HEADER_PREFIXES = (
    "x-google-adk",
    "x-goog-",
    "x-adk",
)

# Sensitive hop-by-hop and credential headers that must never leak downstream
SENSITIVE_FORWARD_HEADERS = {
    "host",
    "content-length",
    "authorization",
    "proxy-authorization",
    "x-forwarded-authorization",
}

MAX_RECURSION_DEPTH = 64


def is_prohibited_key(key: str) -> bool:
    """Check if a dictionary key matches prohibited metadata criteria."""
    if not isinstance(key, str):
        return False
    lower_key = key.lower().strip()
    if lower_key in PROHIBITED_KEYS:
        return True
    if lower_key.startswith("__") or any(lower_key.startswith(prefix) for prefix in PROHIBITED_KEY_PREFIXES):
        return True
    return False


def sanitize_payload(obj: Any, _depth: int = 0) -> Any:
    """Recursively sanitize Python primitives, dictionaries, and lists.

    Removes any dictionary key that matches prohibited ADK metadata fields,
    internal orchestrator traces, system overrides, or credential artifacts.
    Includes bounded recursion depth guard to prevent stack overflow DoS and
    guarantees that payload exceeding maximum depth is safely truncated
    rather than leaking prohibited keys.
    """
    if _depth >= MAX_RECURSION_DEPTH:
        # Bounded depth safeguard to neutralize recursion bombs:
        # If payload exceeds maximum depth, drop un-sanitized child structures to prevent secret leakage
        return {} if isinstance(obj, dict) else ([] if isinstance(obj, list) else None)

    if isinstance(obj, dict):
        cleaned_dict: Dict[str, Any] = {}
        for key, value in obj.items():
            if is_prohibited_key(str(key)):
                continue
            cleaned_dict[key] = sanitize_payload(value, _depth=_depth + 1)
        return cleaned_dict
    elif isinstance(obj, list):
        return [sanitize_payload(item, _depth=_depth + 1) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_payload(item, _depth=_depth + 1) for item in obj)
    elif isinstance(obj, set):
        return {sanitize_payload(item, _depth=_depth + 1) for item in obj}
    elif isinstance(obj, str) and (obj.startswith("{") or obj.startswith("[")):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, (dict, list)):
                sanitized_obj = sanitize_payload(parsed, _depth=_depth + 1)
                return json.dumps(sanitized_obj)
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
        return obj
    else:
        return obj


# Canonical alias mandated by AGENTS.md and AST Micro-Benchmark
sanitize_payload_ast = sanitize_payload


def sanitize_sse_line(line: str) -> str:
    """Sanitize a single line from a Server-Sent Events (SSE) stream.

    Inspects lines starting with 'data:', parses any embedded JSON payload,
    recursively strips prohibited orchestrator and attack keys, and reconstructs
    the sanitized SSE frame.
    """
    stripped = line.strip()
    if not stripped:
        return line
    if stripped.startswith("data:"):
        data_content = stripped[5:].strip()
        if not data_content:
            return line
        try:
            parsed = json.loads(data_content)
            sanitized = sanitize_payload(parsed)
            return f"data: {json.dumps(sanitized)}"
        except Exception:
            return line
    return line


def classify_payload_security(payload: Any) -> Dict[str, Any]:
    """Inspect payload for GxP schema compliance and detect prohibited key presence.
    
    Includes cycle detection and depth boundary safeguards to prevent RecursionError DoS.
    """
    violations: List[str] = []
    seen: Set[int] = set()

    def _inspect(node: Any, path: str = "", depth: int = 0):
        if depth > MAX_RECURSION_DEPTH:
            return
        node_id = id(node)
        if isinstance(node, (dict, list, tuple, set)):
            if node_id in seen:
                return
            seen.add(node_id)
        if isinstance(node, dict):
            for k, v in node.items():
                current_path = f"{path}.{k}" if path else str(k)
                if is_prohibited_key(str(k)):
                    violations.append(current_path)
                _inspect(v, current_path, depth + 1)
        elif isinstance(node, (list, tuple)):
            for idx, item in enumerate(node):
                _inspect(item, f"{path}[{idx}]", depth + 1)

    _inspect(payload)
    return {
        "is_conformant": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
        "gxp_status": "CONFORMANT" if len(violations) == 0 else "CONTAMINATED_PAYLOAD",
    }


def sanitize_headers(
    headers: Union[Dict[str, str], List[tuple]],
    strip_auth: bool = True,
) -> Dict[str, str]:
    """Strip Google ADK headers, hop-by-hop headers, and sensitive upstream authorization.

    Args:
        headers: Incoming HTTP headers.
        strip_auth: When True (default for downstream proxying), strips incoming
            Authorization headers to eliminate confused deputy credential forwarding.
    """
    cleaned: Dict[str, str] = {}

    if isinstance(headers, dict):
        items = headers.items()
    else:
        items = headers

    for key, value in items:
        lower_key = str(key).lower().strip()
        # Check if key starts with any prohibited vendor prefix
        if any(lower_key.startswith(prefix) for prefix in STRIP_HEADER_PREFIXES):
            continue
        # Strip hop-by-hop headers
        if lower_key in {"host", "content-length"}:
            continue
        # Strip authorization headers when forwarding downstream to prevent confused deputy
        if strip_auth and lower_key in SENSITIVE_FORWARD_HEADERS:
            continue
        cleaned[str(key)] = str(value)

    return cleaned
