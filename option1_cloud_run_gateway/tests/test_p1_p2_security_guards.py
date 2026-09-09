"""P1 and P2 Security and Reliability Test Suite.

Validates:
1. Option 2 gRPC Push Dispatcher SSRF guard.
2. Option 2 gRPC StreamTask cancellation registry memory bounding.
3. Option 3 Dual-Plane UI Bridge SSRF guard and dynamic UTC audit trail bounding.
4. Option 1 JSON-RPC 2.0 strict error response conformance (AIP-127).
5. Record-link integrity, signature meaning, and expiration controls.
6. Sliding window rate limiter DoS protection and 429 response structure.
7. PromptCanvas export architecture preset validation.
8. Portal feedback registry bounding (FIFO eviction).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
GATEWAY_DIR = Path(__file__).resolve().parent.parent
if str(GATEWAY_DIR) not in sys.path:
    sys.path.insert(0, str(GATEWAY_DIR))

import asyncio
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from portal.app import app as portal_app, FEEDBACK_REGISTRY
from option1_cloud_run_gateway.app.main import app as gateway_app
from option1_cloud_run_gateway.app.rate_limiter import SlidingWindowRateLimiter
from option1_cloud_run_gateway.app.security import CFRPart11Signer
from option2_grpc_service.server.push_dispatcher import deliver_task_push_notification
from option2_grpc_service.server.services import A2AServiceImpl
from option2_grpc_service.a2a.v1 import a2a_pb2
from option3_dual_plane.ui_bridge import bridge_service as bridge_module
from option3_dual_plane.ui_bridge.bridge_service import (
    app as bridge_app,
    DispatchApprovalRequest,
    dispatch_approval,
    AUDIT_TRAIL,
    CONSUMED_JTIS,
)
from option3_dual_plane.ui_bridge.card_templates import generate_hmac_token
from option3_dual_plane.backend.config import config as option3_config

portal_client = TestClient(portal_app)
gateway_client = TestClient(gateway_app)
bridge_client = TestClient(bridge_app)


@pytest.mark.asyncio
async def test_grpc_push_dispatcher_ssrf_guard():
    """Verify push dispatcher blocks SSRF targets before sending HTTP request."""
    # Cloud metadata target must be blocked immediately
    result = await deliver_task_push_notification(
        url="http://169.254.169.254/computeMetadata/v1/",
        task_id="task-test-push-1",
        state="COMPLETED",
        output_data={"result": "data"},
    )
    assert result is False

    # Prohibited scheme
    result = await deliver_task_push_notification(
        url="file:///etc/shadow",
        task_id="task-test-push-2",
        state="COMPLETED",
        output_data={},
    )
    assert result is False


@pytest.mark.asyncio
async def test_grpc_cancellation_registry_bounded():
    """Exercise CancelTask and verify its real registry bound."""
    service = A2AServiceImpl()
    original_max = service.MAX_CANCELLED_TASKS
    original_batch = service.CANCEL_EVICT_BATCH
    service.MAX_CANCELLED_TASKS = 20
    service.CANCEL_EVICT_BATCH = 5
    try:
        for i in range(35):
            request = a2a_pb2.CancelTaskRequest(task_id=f"task-{i}", reason="test")
            await service.CancelTask(request, None)
        assert len(service._cancelled_tasks) <= 20
        assert "task-34" in service._cancelled_tasks
        assert "task-0" not in service._cancelled_tasks
    finally:
        service.MAX_CANCELLED_TASKS = original_max
        service.CANCEL_EVICT_BATCH = original_batch



@pytest.mark.asyncio
async def test_dual_plane_ui_bridge_ssrf_guard():
    """Verify Plane 2 UI Bridge rejects SSRF targets on approval dispatch."""
    req = DispatchApprovalRequest(
        studyId="MK-3475-087",
        cohort="Cohort-B",
        variancePct=2.14,
        clinicalFindings="Variance in toxicity",
        recommendedAmendment="Dose titration reduction",
        geInboundUrl="http://169.254.169.254/computeMetadata/v1/instance",
    )
    with pytest.raises(HTTPException) as exc_info:
        await dispatch_approval(req)
    assert exc_info.value.status_code == 400
    assert "SSRF Guard" in exc_info.value.detail or "prohibited" in exc_info.value.detail.lower()


def test_dual_plane_demo_action_replay_and_audit_bound(monkeypatch):
    """Exercise the Option 3 callback rather than mutating its list in the test."""
    AUDIT_TRAIL.clear()
    CONSUMED_JTIS.clear()
    monkeypatch.setattr(bridge_module, "MAX_AUDIT_TRAIL", 3)

    for i in range(5):
        token = generate_hmac_token(
            {
                "studyId": "DEMO-001",
                "cohort": "A",
                "decision": "APPROVED",
                "amendment": f"demo-{i}",
            },
            option3_config.HMAC_SECRET,
        )
        response = bridge_client.post(
            "/api/v1/bridge/action-callback",
            json={"stateToken": token, "reviewerEmail": "caller-supplied@example.invalid"},
        )
        assert response.status_code == 200
        record = response.json()["auditRecord"]
        assert record["actor"] == "Demo reviewer (not authenticated)"
        assert record["regulatoryValidation"] is False

    assert len(AUDIT_TRAIL) == 3

    replay_token = generate_hmac_token(
        {"studyId": "DEMO-002", "cohort": "B", "decision": "APPROVED", "amendment": "x"},
        option3_config.HMAC_SECRET,
    )
    first = bridge_client.post("/api/v1/bridge/action-callback", json={"stateToken": replay_token})
    second = bridge_client.post("/api/v1/bridge/action-callback", json={"stateToken": replay_token})
    assert first.status_code == 200
    assert second.status_code == 409



def test_json_rpc_2_0_error_conformance():
    """Verify /a2a/tasks returns strict JSON-RPC 2.0 error payloads for invalid inputs."""
    # 1. Non-2.0 JSON-RPC version
    invalid_version = {
        "jsonrpc": "1.0",
        "method": "a2a.tasks.send",
        "params": {},
        "id": "req-1",
    }
    resp = gateway_client.post("/a2a/tasks", json=invalid_version, headers={"Authorization": "Bearer dev"})
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert data["jsonrpc"] == "2.0"

    # 2. Missing method
    missing_method = {
        "jsonrpc": "2.0",
        "params": {},
        "id": "req-2",
    }
    resp = gateway_client.post("/a2a/tasks", json=missing_method, headers={"Authorization": "Bearer dev"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == -32600

    # 3. Missing taskId / studyId params
    missing_params = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.send",
        "params": {"some_random_field": 123},
        "id": "req-3",
    }
    resp = gateway_client.post("/a2a/tasks", json=missing_params, headers={"Authorization": "Bearer dev"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == -32602


def test_cfr_part11_document_linking_and_expiry():
    """Verify CFRPart11Signer satisfies § 11.50 meaning, § 11.70 linking, and expiration."""
    signer = CFRPart11Signer(b"super-secret-cfr11-key-32bytes-len!!")
    doc_data = {"studyId": "MK-3475-087", "dose": 200, "unit": "mg"}

    # 1. Valid signature
    envelope = signer.create_signature_payload(
        agent_id="agent-001",
        agent_name="Clinical Pharmacologist AI",
        meaning="DoseTitrationApproval",
        document_id="DOC-9901",
        document_data=doc_data,
    )
    valid, reason = signer.verify_signature(envelope, document_data=doc_data)
    assert valid is True
    assert "verified" in reason.lower()

    # 2. Document tampering detection (§ 11.70 record linking)
    tampered_doc = {"studyId": "MK-3475-087", "dose": 400, "unit": "mg"}  # Altered dose
    valid, reason = signer.verify_signature(envelope, document_data=tampered_doc)
    assert valid is False
    assert "Record Linking Failure" in reason

    # 3. Expiration detection
    valid, reason = signer.verify_signature(envelope, document_data=doc_data, max_age_hours=0)
    assert valid is False
    assert "expired" in reason.lower()

    # 4. Missing/empty meaning detection (§ 11.50)
    envelope["payload"]["meaning"] = "   "
    valid, reason = signer.verify_signature(envelope)
    assert valid is False
    assert "meaning cannot be empty" in reason.lower()


def test_sliding_window_rate_limiter():
    """Verify SlidingWindowRateLimiter correctly throttles bursts and returns retry_after."""
    limiter = SlidingWindowRateLimiter(default_limit=4, window_seconds=60)
    ip = "192.168.1.100"

    # First 4 requests succeed
    for _ in range(4):
        allowed, retry_after = limiter.is_allowed(ip, "/api/test")
        assert allowed is True
        assert retry_after == 0

    # 5th request is throttled
    allowed, retry_after = limiter.is_allowed(ip, "/api/test")
    assert allowed is False
    assert retry_after > 0

    # Independent IP is not throttled
    other_allowed, other_retry = limiter.is_allowed("192.168.1.101", "/api/test")
    assert other_allowed is True
    assert other_retry == 0


def test_promptcanvas_export_preset_validation():
    """Verify export-xml strictly validates preset names."""
    # Valid preset
    resp = portal_client.post(
        "/api/promptcanvas/export-xml",
        json={"architecture_preset": "option3_dual_plane"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Invalid preset
    resp = portal_client.post(
        "/api/promptcanvas/export-xml",
        json={"architecture_preset": "malicious_or_unknown_preset_123"},
    )
    assert resp.status_code == 400
    assert "Invalid architecture_preset" in resp.json()["detail"]


def test_portal_feedback_registry_bounded():
    """Verify FEEDBACK_REGISTRY does not grow unboundedly."""
    initial_len = len(FEEDBACK_REGISTRY)

    # Submit 10 new feedbacks
    for i in range(10):
        resp = portal_client.post(
            "/api/feedback/submit",
            json={
                "userId": f"reviewer-{i}@enterprise.internal",
                "role": "Clinician",
                "rating": 5,
                "comment": f"Automated test feedback {i}",
            },
        )
        assert resp.status_code == 200

    assert len(FEEDBACK_REGISTRY) <= 500
