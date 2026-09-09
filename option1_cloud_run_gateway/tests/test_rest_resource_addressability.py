"""Quality Gate: REST Resource-Oriented Architecture (ROA) Addressability & HATEOAS Test Suite.

Verifies that every created entity in the A2A Gateway has a unique URI/URL,
supports direct dereferenceability (GET /resource/{id}), and returns HATEOAS _links.
"""

import pytest
from fastapi.testclient import TestClient
from portal.app import app as portal_app
from option1_cloud_run_gateway.app.main import app as gateway_app


@pytest.fixture
def portal_client():
    return TestClient(portal_app)


@pytest.fixture
def gateway_client():
    return TestClient(gateway_app)


def test_swarm_client_roa_addressability(portal_client, gateway_client):
    """Verify POST /api/v1/register returns a unique URI and GET {uri} returns the resource."""
    payload = {
        "client_name": "ROA_Audit_Swarm_Client_01",
        "organization": "Sovereign Therapeutics Corp",
        "security_scheme": "HMAC-SHA256",
        "gateway_target": "https://a2a-gateway-638420508320.us-central1.run.app",
        "signature_manifestation": {
            "supported_meanings": ["ProtocolApproval", "CohortValidation"]
        }
    }

    # Test on Portal App
    resp = portal_client.post("/api/v1/register", json=payload, headers={"Authorization": "Bearer mock-dev-token"})
    assert resp.status_code == 200
    data = resp.json()

    assert "client_id" in data
    assert "uri" in data
    assert data["uri"] == f"/api/v1/swarms/{data['client_id']}"
    assert "_links" in data
    assert data["_links"]["self"]["href"] == data["uri"]
    assert "registration" in data["_links"]

    # Dereference the resource URL (GET /api/v1/swarms/{client_id})
    get_resp = portal_client.get(data["uri"], headers={"Authorization": "Bearer mock-dev-token"})
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["client_id"] == data["client_id"]
    assert get_data["client_name"] == "ROA_Audit_Swarm_Client_01"
    assert get_data["_links"]["self"]["href"] == data["uri"]

    # Dereference registration receipt URL
    reg_url = data["_links"]["registration"]["href"]
    reg_resp = portal_client.get(reg_url, headers={"Authorization": "Bearer mock-dev-token"})
    assert reg_resp.status_code == 200
    assert reg_resp.json()["registration_id"] == data["registration_id"]

    # Test on Cloud Run Gateway App
    gw_resp = gateway_client.post("/api/v1/register", json=payload, headers={"Authorization": "Bearer mock-dev-token"})
    assert gw_resp.status_code == 200
    gw_data = gw_resp.json()
    assert gw_data["uri"] == f"/api/v1/swarms/{gw_data['client_id']}"

    gw_get_resp = gateway_client.get(gw_data["uri"], headers={"Authorization": "Bearer mock-dev-token"})
    assert gw_get_resp.status_code == 200
    assert gw_get_resp.json()["client_id"] == gw_data["client_id"]


def test_signature_receipt_roa_addressability(portal_client, gateway_client):
    """Verify POST /api/v1/verify-signature returns receipt URI and GET {uri} returns the receipt."""
    from option1_cloud_run_gateway.app.security import CFRPart11Signer

    signer = CFRPart11Signer()
    envelope = signer.create_signature_payload(
        agent_id="agent_roa_tester_01",
        agent_name="ROA Integrity Verification Agent",
        meaning="SafetyReview",
        document_id="doc_roa_protocol_99",
        document_data=b"ROA Protocol Safety Dataset Verification",
    )

    verify_payload = {
        **envelope,
        "document_data": "ROA Protocol Safety Dataset Verification",
        "max_age_hours": 72,
    }

    # Test on Portal App
    resp = portal_client.post("/api/v1/verify-signature", json=verify_payload, headers={"Authorization": "Bearer mock-dev-token"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["valid"] is True
    assert "receipt_id" in data
    assert "uri" in data
    assert data["uri"] == f"/api/v1/signatures/{data['receipt_id']}"
    assert "_links" in data
    assert data["_links"]["self"]["href"] == data["uri"]

    # Dereference the receipt URL
    get_resp = portal_client.get(data["uri"], headers={"Authorization": "Bearer mock-dev-token"})
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["receipt_id"] == data["receipt_id"]
    assert get_data["valid"] is True
    assert get_data["control_standard"] == "PART_11_ALIGNED_TECHNICAL_CONTROLS"
    assert get_data["validation_status"] == "PROTOTYPE_NOT_VALIDATED"

    # Test on Gateway App
    gw_resp = gateway_client.post("/api/v1/verify-signature", json=verify_payload, headers={"Authorization": "Bearer mock-dev-token"})
    assert gw_resp.status_code == 200
    gw_data = gw_resp.json()
    assert gw_data["uri"] == f"/api/v1/signatures/{gw_data['receipt_id']}"

    gw_get_resp = gateway_client.get(gw_data["uri"], headers={"Authorization": "Bearer mock-dev-token"})
    assert gw_get_resp.status_code == 200
    assert gw_get_resp.json()["receipt_id"] == gw_data["receipt_id"]


def test_demo_dossier_and_benchmark_resource_labels(portal_client):
    dossier_resp = portal_client.get(
        "/api/v1/dossiers/FDA-AUDIT-2026-A2A-09881",
        headers={"Authorization": "Bearer mock-dev-token"},
    )
    assert dossier_resp.status_code == 200
    dossier_data = dossier_resp.json()
    assert dossier_data["dossier_id"] == "FDA-AUDIT-2026-A2A-09881"
    assert dossier_data["status"] == "DEMO_TEMPLATE"
    assert dossier_data["validation_status"] == "NOT_VALIDATED"

    bench_resp = portal_client.get("/api/v1/benchmarks/live-empirical-01")
    assert bench_resp.status_code == 200
    bench_data = bench_resp.json()
    assert bench_data["benchmark_id"] == "live-empirical-01"
    assert bench_data["status"] == "STORED_ARTIFACT"
    assert bench_data["measurement_status"] == "not-live"


def test_unknown_resources_fail_closed(portal_client):
    headers = {"Authorization": "Bearer mock-dev-token"}
    assert portal_client.get("/api/v1/swarms/does-not-exist", headers=headers).status_code == 404
    assert portal_client.get("/api/v1/registrations/does-not-exist", headers=headers).status_code == 404
    assert portal_client.get("/api/v1/signatures/does-not-exist", headers=headers).status_code == 404
