"""P0 Security Guardrails Test Suite.

Validates:
1. SSRF prevention against cloud metadata and link-local IP targets.
2. Hardcoded secret entropy enforcement in production mode.
3. Bounded JTI nonce cache and TTL-based memory leak pruning.
4. XML DoS and XXE entity injection defenses in PromptCanvas bridge.
5. Dynamic UTC ISO-8601 timestamps for 21 CFR Part 11 regulatory compliance.
"""

from datetime import datetime, timezone
import re
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from portal.app import app as portal_app
from option1_cloud_run_gateway.app.main import app as gateway_app
from option1_cloud_run_gateway.app.config import Settings
from option1_cloud_run_gateway.app.security import (
    is_safe_webhook_url,
    CONSUMED_JTI_REGISTRY,
    _prune_expired_jtis,
    create_state_token,
    reset_jti_registry,
)
from option1_cloud_run_gateway.app.aws_agentcore_bridge import AwsAgentCoreBridge
from option1_cloud_run_gateway.app.sanitizer import sanitize_payload, classify_payload_security
from option1_cloud_run_gateway.app.ledger import DurableAuditLedger
from option3_dual_plane.backend.config import PlaneConfig

portal_client = TestClient(portal_app)
gateway_client = TestClient(gateway_app)


def test_ssrf_guard_blocks_link_local_metadata():
    """Verify that cloud metadata IPs and internal schemes are blocked."""
    # Link-local AWS/GCP metadata IP
    safe, reason = is_safe_webhook_url("http://169.254.169.254/computeMetadata/v1/")
    assert safe is False
    assert "metadata" in reason.lower() or "link-local" in reason.lower()

    # Named metadata hostnames
    safe, reason = is_safe_webhook_url("http://metadata.google.internal/computeMetadata/v1/")
    assert safe is False
    assert "strictly prohibited" in reason.lower() or "metadata" in reason.lower()

    # Prohibited non-http schemes
    safe, reason = is_safe_webhook_url("file:///etc/passwd")
    assert safe is False
    assert "invalid scheme" in reason.lower()

    safe, reason = is_safe_webhook_url("gopher://127.0.0.1:6379")
    assert safe is False


def test_ssrf_guard_rejects_task_dispatch():
    """Verify handle_task_dispatch rejects SSRF targets with HTTP 400."""
    payload = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.send",
        "params": {
            "taskId": "task-ssrf-attack-1",
            "studyId": "MK-3475-001",
            "pushUrl": "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
        },
        "id": "attack-req-1",
    }
    response = gateway_client.post("/a2a/tasks", json=payload, headers={"Authorization": "Bearer mock-dev-token"})
    assert response.status_code == 400
    assert "ssrf guard" in response.text.lower() or "prohibited" in response.text.lower()


def test_production_secret_entropy_guard():
    """Verify that default or weak JWT secrets are blocked in production."""
    # Default secret in production must fail
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="production",
            JWT_SECRET="Enterprise-gxp-clinical-vault-super-secure-hmac-sha256-key-2026",
        )

    # Short/weak secret in production must fail
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="production",
            JWT_SECRET="short-insecure-secret",
        )

    # Strong 32+ char secret in production must succeed
    valid_settings = Settings(
        APP_ENV="production",
        ALLOW_DEV_AUTH=False,
        JWT_SECRET="c0mPl3x_CrYpt0gRapH1c_s3cr3t_f0r_gXp_pr0d_2026!",
    )
    assert valid_settings.APP_ENV == "production"



def test_jti_cache_bounded_pruning():
    """Verify that expired JTI nonces are automatically evicted to prevent memory leaks."""
    reset_jti_registry()
    now_ts = datetime.now(timezone.utc).timestamp()

    # Seed with expired entries
    CONSUMED_JTI_REGISTRY["expired-jti-1"] = now_ts - 3600
    CONSUMED_JTI_REGISTRY["expired-jti-2"] = now_ts - 100
    # Seed with active entry
    CONSUMED_JTI_REGISTRY["active-jti-1"] = now_ts + 7200

    assert len(CONSUMED_JTI_REGISTRY) == 3
    _prune_expired_jtis(now_ts)

    # Expired entries pruned, active remains
    assert "expired-jti-1" not in CONSUMED_JTI_REGISTRY
    assert "expired-jti-2" not in CONSUMED_JTI_REGISTRY
    assert "active-jti-1" in CONSUMED_JTI_REGISTRY


def test_promptcanvas_xxe_and_entity_bomb_blocked():
    """Verify that PromptCanvas XML compiler rejects DOCTYPE and ENTITY expansion attempts."""
    xxe_payload = """<?xml version="1.0"?>
    <!DOCTYPE mxGraphModel [
        <!ENTITY xxe SYSTEM "file:///etc/passwd">
    ]>
    <mxGraphModel>
        <root>
            <mxCell id="0"/>
            <mxCell id="1" parent="0"/>
            <mxCell id="node1" value="&xxe;" vertex="1" parent="1"/>
        </root>
    </mxGraphModel>"""

    response = portal_client.post("/api/promptcanvas/compile-to-dag", json={"drawio_xml": xxe_payload})
    assert response.status_code == 400
    assert "xxe" in response.text.lower() or "entity" in response.text.lower() or "doctype" in response.text.lower()


def test_dynamic_utc_timestamps_iso8601():
    """Verify audit timestamps are dynamically generated UTC ISO-8601 strings (21 CFR § 11.50)."""
    token = create_state_token({
        "taskId": "task-test-audit-1",
        "studyId": "MK-3475-001",
        "cohort": "Cohort-B",
        "decision": "APPROVED",
    })

    response = portal_client.post("/api/option1/test-action", json={"stateToken": token})
    assert response.status_code == 200
    data = response.json()
    verified_at_str = data["audit"]["verifiedAt"]

    # Parse ISO-8601 timestamp and check freshness within 60 seconds
    parsed_dt = datetime.fromisoformat(verified_at_str)
    now_dt = datetime.now(timezone.utc)
    delta_seconds = abs((now_dt - parsed_dt).total_seconds())
    assert delta_seconds < 60, f"Timestamp {verified_at_str} is not fresh UTC (delta: {delta_seconds}s)"
    assert delta_seconds < 60, f"Timestamp {verified_at_str} is not fresh UTC (delta: {delta_seconds}s)"


def test_aws_sigv4_signing_execution():
    """Verify _sign_sigv4 executes cleanly and produces conformant SigV4 authorization."""
    bridge = AwsAgentCoreBridge(
        aws_region="us-east-1",
        access_key_id="AKIAIOSFODNN7EXAMPLE",
        secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )
    headers = bridge._sign_sigv4(
        method="POST",
        host="vpce-0a1b2c3d4e5f6g7h8.agentcore.us-east-1.vpce.amazonaws.com",
        path="/v1/execute",
        payload_bytes=b'{"taskId": "task-001"}',
        date_stamp="20260909",
        amz_date="20260909T180000Z"
    )
    assert "Authorization" in headers
    assert "AWS4-HMAC-SHA256" in headers["Authorization"]
    assert "AKIAIOSFODNN7EXAMPLE/20260909/us-east-1/bedrock-agent-runtime/aws4_request" in headers["Authorization"]
    assert "SignedHeaders=host;x-amz-date" in headers["Authorization"]
    assert headers["x-amz-date"] == "20260909T180000Z"


def test_sanitizer_deep_nesting_no_leak():
    """Verify sanitize_payload truncates at MAX_RECURSION_DEPTH without leaking secrets."""
    deep = {"level": 0}
    curr = deep
    for i in range(1, 100):
        curr["next"] = {"level": i, "__internal_trace__": "LEAK_SECRET_BEYOND_DEPTH_64"}
        curr = curr["next"]

    cleaned = sanitize_payload(deep)
    assert cleaned["level"] == 0

    # Traverse to maximum depth and verify prohibited key is NEVER leaked at any depth
    node = cleaned
    leaked = False
    while isinstance(node, dict) and "next" in node:
        node = node["next"]
        if isinstance(node, dict) and "__internal_trace__" in node:
            leaked = True
            break
    assert leaked is False


def test_sanitizer_circular_reference_handled():
    """Verify classify_payload_security handles self-referential dictionaries without RecursionError."""
    cyclic_dict = {"title": "Clinical Trial Task"}
    cyclic_dict["self_ref"] = cyclic_dict
    cyclic_dict["children"] = [cyclic_dict]

    report = classify_payload_security(cyclic_dict)
    assert report["is_conformant"] is True
    assert report["violation_count"] == 0
    assert report["gxp_status"] == "CONFORMANT"


def test_cors_regex_blocks_spoofed_domains():
    """Verify CORS regex prevents unanchored subdomain attacks."""
    pattern = r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$|^https://[a-zA-Z0-9-]+\.run\.app$"

    # Legitimate origins
    assert bool(re.match(pattern, "https://my-clinical-gateway.run.app")) is True
    assert bool(re.match(pattern, "http://localhost:8090")) is True
    assert bool(re.match(pattern, "http://127.0.0.1:8080")) is True

    # Malicious spoofed origins
    assert bool(re.match(pattern, "https://evil.run.app.attacker.com")) is False
    assert bool(re.match(pattern, "https://run.app.evil.org")) is False
    assert bool(re.match(pattern, "https://my-gateway.run.app.malicious.io")) is False


def test_audit_ledger_begin_immediate_serialization(tmp_path):
    """Verify DurableAuditLedger serializes events and creates valid linear hash chain."""
    db_file = tmp_path / "test_concurrency_ledger.db"
    ledger = DurableAuditLedger(db_path=db_file)

    event_hash1 = ledger.append_audit_event(
        event_type="DOSE_TITRATION",
        actor_id="clinician@enterprise.internal",
        action="APPROVE",
        details={"cohort": "Cohort-B", "dose_mg": 250}
    )
    event_hash2 = ledger.append_audit_event(
        event_type="DOSE_TITRATION",
        actor_id="investigator@enterprise.internal",
        action="SIGN",
        details={"cohort": "Cohort-B", "dose_mg": 250}
    )

    events = ledger.get_recent_audit_events(limit=10)
    assert len(events) >= 2
    assert events[0]["event_hash"] == event_hash2
    assert events[0]["prev_hash"] == event_hash1


def test_iac_generate_request_validation():
    """Verify IacGenerateRequest enforces strict identifier and KMS key regexes to prevent HCL injection."""
    from portal.cloud_connect_router import IacGenerateRequest

    # Valid request
    valid = IacGenerateRequest(
        project_id="valid-project-123",
        vpc_name="vpc-secure_01",
        subnet_name="subnet-01",
        kms_key_id="projects/p1/locations/global/keyRings/r1/cryptoKeys/k1",
        region="us-central1"
    )
    assert valid.project_id == "valid-project-123"

    # HCL injection attempt with quotes and braces
    with pytest.raises(ValidationError):
        IacGenerateRequest(project_id='test" { malicious_hcl = true } //')

    # Bash injection attempt with semicolon
    with pytest.raises(ValidationError):
        IacGenerateRequest(region='us-central1; rm -rf /')

    # Malicious KMS key with newlines
    with pytest.raises(ValidationError):
        IacGenerateRequest(kms_key_id="projects/p1/locations/global\nmalicious")


def test_rate_limiter_prioritizes_x_real_ip():
    """Verify SlidingWindowRateLimiter prioritizes X-Real-IP over client-controlled headers."""
    from option1_cloud_run_gateway.app.rate_limiter import SlidingWindowRateLimiter
    from starlette.datastructures import Headers

    limiter = SlidingWindowRateLimiter()

    class DummyRequest:
        def __init__(self, headers):
            self.headers = Headers(headers)
            self.client = None

    req = DummyRequest({
        "x-real-ip": "203.0.113.195",
        "x-forwarded-for": "10.0.0.1, 10.0.0.2"
    })
    extracted = limiter._get_client_ip(req)
    assert extracted == "203.0.113.195"


def test_agent_teal_cloudbuild_modern_docker_builder():
    """Verify generate_cloudbuild uses us-docker.pkg.dev instead of sunsetted gcr.io."""
    from a2a_sdk.agent_teal_adapter import AgentTealGcpDeployer

    deployer = AgentTealGcpDeployer(agent_file="example_agent.py")
    cloudbuild = deployer.generate_cloudbuild()
    assert "us-docker.pkg.dev/cloud-builders/docker" in cloudbuild
    assert "gcr.io/cloud-builders/docker" not in cloudbuild


@pytest.mark.asyncio
async def test_vertex_client_deterministic_gxp_hash():
    """Verify VertexAIClinicalEngine produces a deterministic calculation hash."""
    from option3_dual_plane.backend.vertex_client import VertexAIClinicalEngine

    engine = VertexAIClinicalEngine()
    res1 = await engine.execute_clinical_reasoning_loop("MK-3475-087", "Cohort-B")
    res2 = await engine.execute_clinical_reasoning_loop("MK-3475-087", "Cohort-B")
    assert res1.gxp_validation_hash.startswith("sha256-")
    assert res1.gxp_validation_hash == res2.gxp_validation_hash
    assert len(res1.gxp_validation_hash) > 10


@pytest.mark.asyncio
async def test_grpc_stream_task_disconnect_handling():
    """Verify StreamTask immediately breaks loop when context.is_active() is False."""
    from option2_grpc_service.server.services import A2AServiceImpl
    from option2_grpc_service.a2a.v1 import a2a_pb2

    service = A2AServiceImpl()
    req = a2a_pb2.ExecuteTaskRequest(
        task_id="task-disc-01"
    )

    class DisconnectedContext:
        def is_active(self):
            return False

    responses = []
    async for resp in service.StreamTask(req, DisconnectedContext()):
        responses.append(resp)

    # Since context is immediately inactive, it should terminate immediately with 0 iterations
    assert len(responses) == 0


def test_a2a_task_cancel_jsonrpc():
    """Verify JSON-RPC a2a.tasks.cancel returns CANCELLED terminal status."""
    payload = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.cancel",
        "params": {"taskId": "task-test-cancel-99", "reason": "Investigator paused study"},
        "id": "req-cancel-01",
    }
    resp = gateway_client.post("/a2a/tasks", json=payload, headers={"Authorization": "Bearer dev-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["taskId"] == "task-test-cancel-99"
    assert data["result"]["status"] == "CANCELLED"
    assert data["result"]["isTerminal"] is True


def test_a2a_task_get_jsonrpc():
    """Verify JSON-RPC a2a.tasks.get returns task status."""
    payload = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.get",
        "params": {"taskId": "task-test-get-88"},
        "id": "req-get-01",
    }
    resp = gateway_client.post("/a2a/tasks", json=payload, headers={"Authorization": "Bearer dev-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["taskId"] == "task-test-get-88"
    assert data["result"]["status"] == "COMPLETED"


def test_a2a_task_dispatch_omnichannel_artifact():
    """Verify standalone task dispatch returns all 4 A2UI dialects in the artifact."""
    payload = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.send",
        "params": {"taskId": "task-omnichannel-01", "studyId": "MK-3475-087", "cohort": "Cohort-B"},
        "id": "req-omni-01",
    }
    resp = gateway_client.post("/a2a/tasks", json=payload, headers={"Authorization": "Bearer dev-token"})
    assert resp.status_code == 200
    data = resp.json()
    artifact = data["result"]["artifact"]
    assert artifact["type"] == "a2ui_surface"
    assert "a2ui" in artifact
    assert "googleCardV2" in artifact
    assert "slackBlockKit" in artifact
    assert "teamsAdaptiveCard" in artifact
    assert "webGlassmorphic" in artifact
    assert artifact["slackBlockKit"] is not None
    assert artifact["teamsAdaptiveCard"] is not None


def test_cloud_connect_dispatch_webhook_ssrf_blocked():
    """Verify /dispatch-webhook endpoint blocks cloud metadata SSRF targets."""
    payload = {
        "target_channel": "google_chat",
        "webhook_url": "http://169.254.169.254/latest/meta-data/",
        "trial_id": "MK-3475-087",
        "cohort": "Cohort-B",
        "proposed_dose_mg": 250.0,
    }
    resp = portal_client.post("/api/connect/dispatch-webhook", json=payload)
    assert resp.status_code == 400
    assert "SSRF Guard" in resp.json()["detail"]
