"""Unit tests for recursive payload and header sanitization.

Verifies zero metadata leakage of Google ADK envelope tags into Enterprise GxP parsers.
"""

import pytest
from app.sanitizer import sanitize_headers, sanitize_payload, is_prohibited_key


def test_is_prohibited_key():
    assert is_prohibited_key("adk_metadata") is True
    assert is_prohibited_key("_adk") is True
    assert is_prohibited_key("ge_context") is True
    assert is_prohibited_key("agent_metadata") is True
    assert is_prohibited_key("__adk_trace_id") is True
    assert is_prohibited_key("__adk_system_prompt") is True
    assert is_prohibited_key("ADK_METADATA") is True

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

    # Ensure clinical payload integrity is 100% preserved
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

    # Required headers retained
    assert clean_headers["Authorization"] == "Bearer mock-token"
    assert clean_headers["Content-Type"] == "application/json"
    assert clean_headers["X-Enterprise-Trace-Id"] == "Enterprise-12345"
