"""P0 Security Guardrails Test Suite.

Validates:
1. SSRF prevention against cloud metadata and link-local IP targets.
2. Hardcoded secret entropy enforcement in production mode.
3. Bounded JTI nonce cache and TTL-based memory leak pruning.
4. XML DoS and XXE entity injection defenses in PromptCanvas bridge.
5. Dynamic UTC ISO-8601 timestamps for 21 CFR Part 11 regulatory compliance.
"""

from datetime import datetime, timezone
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
