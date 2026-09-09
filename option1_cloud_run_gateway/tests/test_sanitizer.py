"""Unit tests for gateway policy sanitization.

These tests cover a finite adversarial corpus; they do not claim universal
zero-leakage or regulatory validation.
"""

import pytest
from option1_cloud_run_gateway.app.sanitizer import (
    is_prohibited_key,
    sanitize_a2a_envelope,
    sanitize_headers,
    sanitize_payload,
    sanitize_sse_event,
)


def test_is_prohibited_key():
    assert is_prohibited_key("adk_metadata") is True
    assert is_prohibited_key("_adk") is True
    assert is_prohibited_key("ge_context") is True
    assert is_prohibited_key("agent_metadata") is True
    assert is_prohibited_key("__adk_trace_id") is True
    assert is_prohibited_key("__adk_system_prompt") is True
    assert is_prohibited_key("ADK_METADATA") is True
    assert is_prohibited_key("__internal_trace__") is True
    assert is_prohibited_key("system_override") is True
    assert is_prohibited_key("access_token") is True
    assert is_prohibited_key("client_secret") is True

    # Valid clinical fields must NOT be stripped
    assert is_prohibited_key("studyId") is False
    assert is_prohibited_key("cohort") is False
    assert is_prohibited_key("patient_id") is False
    assert is_prohibited_key("adverse_events") is False


def test_sanitize_nested_payload():
    contaminated_payload = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.send",
        "adk_metadata": {
            "model": "gemini-1.5-pro",
            "temperature": 0.2,
            "system_instruction_hash": "a1b2c3d4",
        },
        "_adk": {"envelope_version": "v1alpha"},
        "ge_context": {"session_id": "ge-sess-9999"},
        "params": {
            "taskId": "task-clin-001",
            "studyId": "MK-3475-087",
            "cohort": "Cohort-B",
            "__adk_internal_trace": "trace-uuid-1234",
            "data": {
                "variance": 2.14,
                "agent_metadata": {"router_agent": "Enterprise-supervisor"},
                "sub_items": [
                    {
                        "findingId": "F-01",
                        "adk_metadata": "leakage",
                        "status": "VALIDATED",
                    },
                    {
                        "findingId": "F-02",
                        "__adk_tokens": 450,
                        "status": "VALIDATED",
                    },
                ],
            },
        },
        "id": "req-001",
    }

    cleaned = sanitize_payload(contaminated_payload)

    # Ensure prohibited keys are completely gone
    assert "adk_metadata" not in cleaned
    assert "_adk" not in cleaned
    assert "ge_context" not in cleaned
    assert "__adk_internal_trace" not in cleaned["params"]
    assert "agent_metadata" not in cleaned["params"]["data"]
    assert "adk_metadata" not in cleaned["params"]["data"]["sub_items"][0]
    assert "__adk_tokens" not in cleaned["params"]["data"]["sub_items"][1]

    # Ensure declared business payload fields used by this corpus are preserved
    assert cleaned["jsonrpc"] == "2.0"
    assert cleaned["id"] == "req-001"
    assert cleaned["params"]["taskId"] == "task-clin-001"
    assert cleaned["params"]["studyId"] == "MK-3475-087"
    assert cleaned["params"]["cohort"] == "Cohort-B"
    assert cleaned["params"]["data"]["variance"] == 2.14
    assert cleaned["params"]["data"]["sub_items"][0]["findingId"] == "F-01"
    assert cleaned["params"]["data"]["sub_items"][0]["status"] == "VALIDATED"


def test_sanitize_headers():
    dirty_headers = {
        "Host": "gateway.enterprise.internal",
        "Content-Length": "1024",
        "Authorization": "Bearer mock-token",
        "Content-Type": "application/json",
        "X-Google-ADK-Trace": "goog-trace-999",
        "X-Goog-User-Project": "ge-production-cloud",
        "x-adk-session": "sess-443",
        "X-Enterprise-Trace-Id": "Enterprise-12345",
    }

    clean_headers = sanitize_headers(dirty_headers)

    assert "X-Google-ADK-Trace" not in clean_headers
    assert "X-Goog-User-Project" not in clean_headers
    assert "x-adk-session" not in clean_headers
    assert "Host" not in clean_headers
    assert "Content-Length" not in clean_headers

    # Caller credentials must never be forwarded downstream.
    assert "Authorization" not in clean_headers
    assert clean_headers["Content-Type"] == "application/json"
    assert clean_headers["X-Enterprise-Trace-Id"] == "Enterprise-12345"



def test_a2a_envelope_allowlist_and_secret_removal():
    payload = {
        "jsonrpc": "2.0",
        "method": "SendMessage",
        "id": "1",
        "system_override": "do-not-forward",
        "unexpected_wrapper": {"value": "do-not-forward"},
        "params": {
            "message": {
                "messageId": "m-1",
                "role": "ROLE_USER",
                "parts": [{"text": "hello"}],
                "metadata": {
                    "access_token": "sensitive-token-value",
                    "__internal_trace__": "trace-value",
                    "studyId": "DEMO-1",
                },
            }
        },
    }
    cleaned = sanitize_a2a_envelope(payload)
    assert "system_override" not in cleaned
    assert "unexpected_wrapper" not in cleaned
    serialized = str(cleaned)
    assert "sensitive-token-value" not in serialized
    assert "trace-value" not in serialized
    assert cleaned["params"]["message"]["metadata"]["studyId"] == "DEMO-1"


def test_sse_json_frames_are_sanitized():
    event = (
        b"id: 7\n"
        b"event: status-update\n"
        b'data: {"result":{"status":"working","access_token":"secret-value","studyId":"DEMO"}}\n\n'
    )
    cleaned = sanitize_sse_event(event)
    assert b"secret-value" not in cleaned
    assert b"access_token" not in cleaned
    assert b'"studyId":"DEMO"' in cleaned


def test_sse_non_json_data_fails_closed():
    with pytest.raises(ValueError, match="Non-JSON SSE"):
        sanitize_sse_event(b"data: opaque-secret-stream\n\n")
