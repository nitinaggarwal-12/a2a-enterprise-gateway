"""End-to-End integration tests for Option 1: Cloud Run Interceptor Gateway.

Tests:
1. Discovery /.well-known/agent.json
2. Health check /healthz
3. Task dispatch with ADK envelope -> Sanitization -> INPUT_REQUIRED response with A2UI artifact
4. Interactive UI Action submission with HMAC state token -> Stateless validation -> Output & Push
5. State token tampering detection (security validation)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import create_state_token, verify_state_token


@pytest.fixture
def client():
    return TestClient(app)


def test_discovery_endpoint(client):
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["schemaVersion"] == "1.0.0"
    assert data["protocolVersion"] == "1.0.0"
    assert data["capabilities"]["gxpSanitization"] is True
    assert data["capabilities"]["streaming"] is True
    assert data["capabilities"]["stateTokens"] is True
    assert data["capabilities"]["a2ui"] is True
    assert "a2ui.v1" in data["supportedDialects"]


def test_healthz_endpoint(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_task_dispatch_and_a2ui_generation(client):
    # Simulated GE task request contaminated with proprietary ADK metadata
    ge_task_request = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.send",
        "adk_metadata": {
            "model_version": "gemini-1.5-pro-002",
            "system_instruction_crc": "9a8b7c",
        },
        "_adk": {"envelope": "alpha"},
        "params": {
            "taskId": "task-clin-101",
            "studyId": "MK-3475-001",
            "cohort": "Cohort-B",
            "pushUrl": "https://ge-mock.internal.enterprise.internal/webhook/notify",
            "__adk_trace": "internal-trace-001",
        },
        "id": "rpc-test-01",
    }

    headers = {
        "Authorization": "Bearer mock-dev-token",
        "X-Google-ADK-Session": "sess-ge-99",
        "Content-Type": "application/json",
    }

    response = client.post("/a2a/tasks", json=ge_task_request, headers=headers)
    assert response.status_code == 200
    res_data = response.json()

    assert res_data["jsonrpc"] == "2.0"
    assert res_data["id"] == "rpc-test-01"
    result = res_data["result"]
    assert result["taskId"] == "task-clin-101"
    assert result["status"] == "INPUT_REQUIRED"

    # Verify A2UI surface structure
    artifact = result["artifact"]
    assert artifact["type"] == "a2ui_surface"
    a2ui = artifact["a2ui"]
    assert a2ui["surfaceType"] == "a2ui_card"
    assert len(a2ui["actions"]) == 2

    # Extract state tokens
    approve_action = next(a for a in a2ui["actions"] if a["id"] == "action_approve")
    reject_action = next(a for a in a2ui["actions"] if a["id"] == "action_reject")

    assert approve_action["stateToken"] is not None
    assert reject_action["stateToken"] is not None

    # Statelessly verify token claims
    claims = verify_state_token(approve_action["stateToken"])
    assert claims["taskId"] == "task-clin-101"
    assert claims["studyId"] == "MK-3475-001"
    assert claims["cohort"] == "Cohort-B"
    assert claims["decision"] == "APPROVED"
    assert claims["pushUrl"] == "https://ge-mock.internal.enterprise.internal/webhook/notify"


def test_ui_action_stateless_execution(client):
    # Create sealed state token
    state_token = create_state_token({
        "taskId": "task-clin-202",
        "studyId": "MK-8888-002",
        "cohort": "Cohort-A",
        "decision": "APPROVED",
        "pushUrl": "https://ge-mock.internal.enterprise.internal/webhook/notify",
    })

    action_request = {
        "jsonrpc": "2.0",
        "method": "a2a.ui.action",
        "params": {
            "stateToken": state_token,
        },
        "id": "rpc-action-01",
    }

    headers = {
        "Authorization": "Bearer mock-dev-token",
        "Content-Type": "application/json",
    }

    response = client.post("/a2a/ui/action", json=action_request, headers=headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]

    assert result["taskId"] == "task-clin-202"
    assert result["status"] == "COMPLETED"
    assert result["decision"] == "APPROVED"
    assert result["studyId"] == "MK-8888-002"
    assert result["cohort"] == "Cohort-A"
    assert result["stateVerified"] is True
    assert result["audit"]["gxPCompliant"] is True


def test_state_token_tampering_rejection(client):
    valid_token = create_state_token({
        "taskId": "task-clin-303",
        "studyId": "MK-9999",
        "cohort": "Cohort-C",
        "decision": "APPROVED",
    })

    # Tamper with token payload
    tampered_token = valid_token[:-4] + "fake"

    action_request = {
        "jsonrpc": "2.0",
        "method": "a2a.ui.action",
        "params": {
            "stateToken": tampered_token,
        },
        "id": "rpc-action-tamper",
    }

    headers = {"Authorization": "Bearer mock-dev-token"}
    response = client.post("/a2a/ui/action", json=action_request, headers=headers)
    assert response.status_code == 400
    assert "Tampered or invalid state token signature" in response.json()["detail"]


def test_a2ui_omnichannel_transpilation():
    from app.a2ui_builder import get_a2ui_preset_templates, transpile_a2ui_to_all

    templates = get_a2ui_preset_templates()
    assert "dose_titration" in templates
    assert "pv_e2b_expedited" in templates
    assert "lab_data_grid" in templates
    assert "gmp_batch_capa" in templates

    dose_tpl = templates["dose_titration"]
    transpiled = transpile_a2ui_to_all(dose_tpl, unblind=False)
    assert transpiled["googleCardV2"] is not None
    assert transpiled["slackBlockKit"] is not None
    assert transpiled["teamsAdaptiveCard"] is not None
    assert transpiled["webGlassmorphic"] is not None
    assert len(transpiled["canonicalA2UI"]["actions"]) >= 1


def test_a2ui_jti_nonce_idempotency_guard():
    from app.security import create_state_token, consume_state_token, reset_jti_registry
    from fastapi import HTTPException

    reset_jti_registry()
    token = create_state_token({
        "taskId": "task-jti-test-01",
        "decision": "APPROVED",
    })

    # First consumption must succeed
    claims1 = consume_state_token(token)
    assert claims1["decision"] == "APPROVED"
    assert "jti" in claims1

    # Second consumption (replay attack) must raise HTTPException 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        consume_state_token(token)
    assert exc_info.value.status_code == 409
    assert "has already been consumed" in exc_info.value.detail

