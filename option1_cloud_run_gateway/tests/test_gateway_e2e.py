"""End-to-End integration tests for Option 1: Cloud Run Interceptor Gateway.

Tests:
1. A2A v1 discovery /.well-known/agent-card.json
2. Health check /healthz
3. Task dispatch with ADK envelope -> Sanitization -> INPUT_REQUIRED response with A2UI artifact
4. Interactive UI Action submission with HMAC state token -> Stateless validation -> Output & Push
5. State token tampering detection (security validation)
"""

import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
GATEWAY_DIR = Path(__file__).resolve().parent.parent
if str(GATEWAY_DIR) not in sys.path:
    sys.path.insert(0, str(GATEWAY_DIR))

import pytest
from fastapi.testclient import TestClient
from option1_cloud_run_gateway.app.main import app
from option1_cloud_run_gateway.app.security import create_state_token, verify_state_token


@pytest.fixture
def client():
    return TestClient(app)


def test_discovery_endpoint(client):
    response = client.get("/.well-known/agent-card.json")
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Enterprise A2A Policy Gateway"
    assert data["supportedInterfaces"][0]["protocolBinding"] == "JSONRPC"
    assert data["supportedInterfaces"][0]["protocolVersion"] == "1.0"
    assert data["capabilities"]["streaming"] is False
    assert data["capabilities"]["pushNotifications"] is False
    assert data["capabilities"]["extendedAgentCard"] is False
    assert data["skills"]

    legacy = client.get("/.well-known/agent.json", follow_redirects=False)
    assert legacy.status_code == 308
    assert legacy.headers["location"] == "/.well-known/agent-card.json"


def test_a2a_v1_version_negotiation_and_send_message(client):
    payload = {
        "jsonrpc": "2.0",
        "id": "a2a-v1-1",
        "method": "SendMessage",
        "params": {
            "message": {
                "messageId": "msg-1",
                "role": "ROLE_USER",
                "parts": [{"text": "Review demo study"}],
                "metadata": {"studyId": "DEMO-001", "cohort": "A"},
            }
        },
    }
    headers = {
        "Authorization": "Bearer mock-dev-token",
        "A2A-Version": "1.0",
    }
    response = client.post("/a2a/v1", json=payload, headers=headers)
    assert response.status_code == 200
    task = response.json()["result"]["task"]
    assert task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"
    assert task["metadata"]["regulatedUse"] == "not-validated"

    unsupported = client.post(
        "/a2a/v1",
        json=payload,
        headers={"Authorization": "Bearer mock-dev-token", "A2A-Version": "1.0.0"},
    )
    assert unsupported.status_code == 400
    assert unsupported.json()["error"]["code"] == -32009


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
    assert result["audit"]["controlEvidenceGenerated"] is True
    assert result["audit"]["validationStatus"] == "prototype-not-validated"


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
    from option1_cloud_run_gateway.app.a2ui_builder import get_a2ui_preset_templates, transpile_a2ui_to_all

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
    from option1_cloud_run_gateway.app.security import create_state_token, consume_state_token, reset_jti_registry
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


def test_a2ui_form_controls_and_deviation_template():
    from option1_cloud_run_gateway.app.a2ui_builder import get_a2ui_preset_templates, transpile_a2ui_to_all

    templates = get_a2ui_preset_templates()
    assert "protocol_deviation_triage" in templates

    dev_tpl = templates["protocol_deviation_triage"]
    sections = dev_tpl["a2ui"]["sections"]
    sec_types = [s.get("type") for s in sections]
    assert "key_value_grid" in sec_types
    assert "callout_box" in sec_types
    assert "dropdown_select" in sec_types
    assert "radio_group" in sec_types
    assert "text_input" in sec_types
    assert "date_picker" in sec_types

    transpiled = transpile_a2ui_to_all(dev_tpl, unblind=False)

    # 1. Google Workspace Card v2 Verification
    g_card = transpiled["googleCardV2"]
    widgets = []
    for s in g_card["card"]["sections"]:
        widgets.extend(s.get("widgets", []))
    has_text_input = any("textInput" in w for w in widgets)
    has_selection = any("selectionInput" in w for w in widgets)
    has_date = any("dateTimePicker" in w for w in widgets)
    assert has_text_input, "Google Card v2 must contain textInput widget"
    assert has_selection, "Google Card v2 must contain selectionInput widget"
    assert has_date, "Google Card v2 must contain dateTimePicker widget"

    # 2. Slack Block Kit Verification
    s_blocks = transpiled["slackBlockKit"]["blocks"]
    input_blocks = [b for b in s_blocks if b.get("type") == "input"]
    element_types = [b.get("element", {}).get("type") for b in input_blocks]
    assert "plain_text_input" in element_types, "Slack Block Kit must contain plain_text_input"
    assert "static_select" in element_types, "Slack Block Kit must contain static_select"
    assert "radio_buttons" in element_types, "Slack Block Kit must contain radio_buttons"
    assert "datepicker" in element_types, "Slack Block Kit must contain datepicker"

    # 3. Teams Adaptive Card Verification
    t_items = transpiled["teamsAdaptiveCard"]["body"]
    item_types = [it.get("type") for it in t_items]
    assert "Input.Text" in item_types, "Teams Adaptive Card must contain Input.Text"
    assert "Input.ChoiceSet" in item_types, "Teams Adaptive Card must contain Input.ChoiceSet"
    assert "Input.Date" in item_types, "Teams Adaptive Card must contain Input.Date"

    # 4. Web Glassmorphic Verification
    web_sections = transpiled["webGlassmorphic"]["sections"]
    web_types = [s.get("type") for s in web_sections]
    assert "key_value_grid" in web_types
    assert "dropdown_select" in web_types
    assert "radio_group" in web_types
    assert "text_input" in web_types
    assert "date_picker" in web_types


def test_ui_action_with_form_inputs_and_replay_guard(client):
    from option1_cloud_run_gateway.app.security import create_state_token, reset_jti_registry

    reset_jti_registry()
    token = create_state_token({
        "taskId": "task-deviation-999",
        "studyId": "MK-3475-087",
        "cohort": "Cohort-B",
        "decision": "APPROVED",
    })

    action_request = {
        "jsonrpc": "2.0",
        "method": "a2a.ui.action",
        "params": {
            "stateToken": token,
            "formInputs": {
                "deviationSeverity": "Major",
                "recommendedAction": "Maintain Patient on Reduced Dose",
                "justificationRationale": "Liver enzymes AST/ALT remain within normal range; patient cleared for continuation.",
                "followUpDate": "2026-09-12",
            },
            "justification": "Liver enzymes AST/ALT remain within normal range; patient cleared for continuation.",
        },
        "id": "rpc-action-form-test",
    }

    headers = {"Authorization": "Bearer mock-dev-token"}

    # 1. First Execution: must succeed (HTTP 200)
    resp1 = client.post("/a2a/ui/action", json=action_request, headers=headers)
    assert resp1.status_code == 200
    res1 = resp1.json()["result"]
    assert res1["status"] == "COMPLETED"
    assert res1["decision"] == "APPROVED"
    assert res1["formInputs"]["deviationSeverity"] == "Major"
    assert "Liver enzymes" in res1["justification"]
    assert res1["audit"]["controlEvidenceGenerated"] is True
    assert res1["audit"]["validationStatus"] == "prototype-not-validated"

    # 2. Second Execution (Replay Attack): must be rejected with HTTP 409 Conflict
    resp2 = client.post("/a2a/ui/action", json=action_request, headers=headers)
    assert resp2.status_code == 409
    assert "has already been consumed" in resp2.json()["detail"]


def test_portal_a2ui_action_and_electronic_signature():
    from portal.app import app as portal_app
    from option1_cloud_run_gateway.app.security import create_state_token

    portal_client = TestClient(portal_app)

    # 1. Template registry
    tpl_resp = portal_client.get("/api/a2ui/templates")
    assert tpl_resp.status_code == 200
    templates = tpl_resp.json()["templates"]
    assert "protocol_deviation_triage" in templates

    # 2. Execute Action with Justification & Form Inputs
    token = create_state_token({
        "taskId": "task-portal-test-42",
        "studyId": "MK-3475-087",
        "cohort": "Cohort-B",
        "decision": "APPROVED",
    })

    action_payload = {
        "stateToken": token,
        "actionId": "action_approve_deviation",
        "formInputs": {
            "deviationSeverity": "Major",
            "recommendedAction": "Maintain Patient on Reduced Dose",
            "justificationRationale": "Subject tolerating reduced dose well with normal liver enzymes.",
            "followUpDate": "2026-09-12",
        },
        "justification": "Subject tolerating reduced dose well with normal liver enzymes.",
        "signerName": "Dr. Nitin Aggarwal, MD",
        "signerRole": "Global Medical Monitor",
        "signatureMeaning": "Approval of Clinical Protocol Amendment & Patient Disposition (21 CFR Part 11 § 11.50)",
    }

    resp1 = portal_client.post("/api/a2ui/action", json=action_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is True
    assert data1["status"] == "COMPLETED"
    assert data1["decision"] == "APPROVED"
    assert "approvalMarker" in data1
    assert data1["approvalMarker"]["actor"] == "Demo reviewer (not authenticated)"
    assert data1["approvalMarker"]["cryptographicSignatureCreated"] is False
    assert data1["approvalMarker"]["regulatoryValidation"] is False

    # Check platform-native responses
    platforms = data1["platformResponses"]
    assert "googleWorkspace" in platforms
    assert "slackBlockKit" in platforms
    assert "teamsAdaptiveCard" in platforms
    assert platforms["googleWorkspace"]["actionResponse"]["type"] == "UPDATE_MESSAGE"
    assert platforms["slackBlockKit"]["replace_original"] is True
    assert platforms["teamsAdaptiveCard"]["type"] == "AdaptiveCard"

    # 3. Replay rejection
    resp2 = portal_client.post("/api/a2ui/action", json=action_payload)
    assert resp2.status_code == 409
    data2 = resp2.json()
    assert data2["success"] is False
    assert data2["status"] == "CONFLICT"
    assert data2["idempotencyTriggered"] is True

    # 4. Reset idempotency
    reset_resp = portal_client.post(
        "/api/a2ui/reset-idempotency",
        headers={"Authorization": "Bearer mock-dev-token"},
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True


def test_swarm_client_registration(client):
    """Test sovereign biopharma swarm registration payload specified in 21 CFR Part 11 blueprint."""
    reg_payload = {
        "client_name": "Sovereign_Biopharma_Cohort_Swarm_01",
        "organization": "Sovereign Therapeutics Corp",
        "gateway_target": "https://a2a-gateway-638420508320.us-central1.run.app",
        "security_scheme": "HMAC-SHA256",
        "compliance_frameworks": ["21_CFR_Part_11", "Annex_11"],
        "signature_manifestation": {
            "supported_meanings": [
                "ProtocolApproval",
                "CohortValidation",
                "SafetyReview",
                "SystemAudit"
            ]
        }
    }
    response = client.post(
        "/api/v1/register",
        json=reg_payload,
        headers={"Authorization": "Bearer mock-dev-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REGISTERED"
    assert data["client_name"] == "Sovereign_Biopharma_Cohort_Swarm_01"
    assert data["compliance_status"] == "CONTROL_PROTOTYPE_NOT_VALIDATED"
    assert "CohortValidation" in data["supported_meanings"]
    assert data["verification_endpoint"] == "/api/v1/verify-signature"


def test_swarm_stateless_signature_verification_and_tamper_guard(client):
    """Test CFRPart11Signer envelope verification and cyber-tamper detection."""
    from option1_cloud_run_gateway.app.security import CFRPart11Signer

    signer = CFRPart11Signer()
    protocol_doc = b"CLINICAL TRIAL PROTOCOL: Phase IIa sovereign mRNA target mapping..."

    signed_envelope = signer.create_signature_payload(
        agent_id="agent_cohort_matcher_04",
        agent_name="Autonomous Cohort Matching Agent (v2.1)",
        meaning="CohortValidation",
        document_id="protocol_amendment_v3.2",
        document_data=protocol_doc,
    )

    # 1. Valid Signature Verification
    verify_payload = {
        **signed_envelope,
        "document_data": protocol_doc.decode("utf-8"),
        "max_age_hours": 72,
    }
    verify_resp = client.post(
        "/api/v1/verify-signature",
        json=verify_payload,
        headers={"Authorization": "Bearer mock-dev-token"},
    )
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["valid"] is True
    assert v_data["signer_id"] == "agent_cohort_matcher_04"
    assert v_data["meaning"] == "CohortValidation"
    assert v_data["control_standard"] == "PART_11_ALIGNED_TECHNICAL_CONTROLS"
    assert v_data["validation_status"] == "PROTOTYPE_NOT_VALIDATED"

    # 2. Tamper Attack (Attacker alters document_id or hash)
    tampered_envelope = dict(signed_envelope)
    tampered_envelope["payload"] = dict(signed_envelope["payload"])
    tampered_envelope["payload"]["document_id"] = "protocol_amendment_tampered"

    tampered_payload = {
        **tampered_envelope,
        "document_data": protocol_doc.decode("utf-8"),
        "max_age_hours": 72,
    }
    tamper_resp = client.post(
        "/api/v1/verify-signature",
        json=tampered_payload,
        headers={"Authorization": "Bearer mock-dev-token"},
    )
    assert tamper_resp.status_code == 401
    assert "verification failed" in tamper_resp.json()["detail"].lower()




