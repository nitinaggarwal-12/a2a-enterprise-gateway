"""Sanitizer module for stripping proprietary Google ADK metadata and envelope headers.

Enterprise GxP validation parsers (21 CFR Part 11 strict schema compliance) require
complete elimination of undeclared metadata fields and vendor-specific envelopes.
"""

from typing import Any, Dict, List, Set, Union


# Prohibited metadata keys exact match set
PROHIBITED_KEYS: Set[str] = {
    "adk_metadata",
    "_adk",
    "ge_context",
    "agent_metadata",
}

# Header prefixes to strip before reverse-proxying downstream
STRIP_HEADER_PREFIXES = (
    "x-google-adk",
    "x-goog-",
    "x-adk",
)


def is_prohibited_key(key: str) -> bool:
    """Check if a dictionary key matches prohibited metadata criteria."""
    if not isinstance(key, str):
        return False
    lower_key = key.lower().strip()
    if lower_key in PROHIBITED_KEYS:
        return True
    if lower_key.startswith("__adk"):
        return True
    return False


def sanitize_payload(obj: Any) -> Any:
    """Recursively sanitize Python primitives, dictionaries, and lists.

    Removes any dictionary key that matches prohibited ADK metadata fields
    or starts with '__adk'.
    """
    if isinstance(obj, dict):
        cleaned_dict: Dict[str, Any] = {}
        for key, value in obj.items():
            if is_prohibited_key(str(key)):
                continue
            cleaned_dict[key] = sanitize_payload(value)
        return cleaned_dict
    elif isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_payload(item) for item in obj)
    elif isinstance(obj, set):
        return {sanitize_payload(item) for item in obj}
    else:
        return obj


def sanitize_headers(headers: Union[Dict[str, str], List[tuple]]) -> Dict[str, str]:
    """Strip all incoming HTTP headers starting with x-google-adk, x-goog-, or x-adk.

    Also ensures hop-by-hop headers like host/content-length are handled cleanly.
    """
    cleaned: Dict[str, str] = {}

    if isinstance(headers, dict):
        items = headers.items()
    else:
        items = headers

    for key, value in items:
        lower_key = str(key).lower().strip()
        # Check if key starts with any prohibited prefix
        if any(lower_key.startswith(prefix) for prefix in STRIP_HEADER_PREFIXES):
            continue
        # Strip hop-by-hop headers if forwarding
        if lower_key in {"host", "content-length"}:
            continue
        cleaned[str(key)] = str(value)

    return cleaned
