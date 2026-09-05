"""Unit & Integration tests for Cloud Connect & Onboarding Router.

Tests all 6 onboarding pillars:
1. Architecture Matchmaker (Recommends Archetype, Pattern, and Setup Time)
2. Live Infrastructure-as-Code Generator (Terraform, Helm, gcloud)
3. Real-Time Network & Security Diagnostics Suite (mTLS, PSC, AST, KMS)
4. CDISC SDTM Sandbox & Zero-PHI Preflight Engine
5. In-Situ Collaboration Webhook Switchboard (A2UI Interactive Cards)
6. 1-Click Infosec & 21 CFR Part 11 Compliance Dossier Export
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from fastapi.testclient import TestClient
from portal.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_matchmaker_dual_plane_psc(client):
    payload = {
        "cloud_provider": "gcp",
        "data_lake": "bigquery",
        "compliance_tier": "part11_gxp",
        "tenant_name": "Merck Oncology R&D"
    }
    response = client.post("/api/connect/matchmaker", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Dual-Plane" in data["recommendedArchetype"]
    assert "Private Service Connect" in data["recommendedPattern"]
    assert data["selectedCloud"] == "GCP"
    assert "FDA 21 CFR Part 11" in data["complianceStandards"]


def test_matchmaker_enclave_zkp(client):
    payload = {
        "cloud_provider": "aws",
        "data_lake": "snowflake",
        "compliance_tier": "consortium_zkp",
        "tenant_name": "Cross-Hospital Oncology Consortium"
    }
    response = client.post("/api/connect/matchmaker", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Confidential Enclave" in data["recommendedArchetype"]
    assert "zk-SNARKs" in data["recommendedPattern"]
    assert "0 Raw Records" in data["dataMovement"]


def test_generate_iac_terraform_and_helm(client):
    payload = {
        "project_id": "roche-clinical-mesh-prod",
        "vpc_name": "vpc-roche-clinical",
        "subnet_name": "sb-clinical-eu-west3",
        "kms_key_id": "projects/roche-clinical-mesh-prod/locations/europe-west3/keyRings/hsm/cryptoKeys/cfr11",
        "region": "europe-west3"
    }
    response = client.post("/api/connect/generate-iac", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "google_compute_forwarding_rule" in data["terraform"]
    assert "roche-clinical-mesh-prod" in data["terraform"]
    assert "DEPLOYMENT_ARCHETYPE" in data["helmValues"]
    assert "gcloud compute forwarding-rules create" in data["gcloudOneLiner"]


def test_network_diagnostics_suite(client):
    payload = {
        "target_endpoint": "psc://10.128.0.50:50051",
        "run_payload_probe": True
    }
    response = client.post("/api/connect/test-diagnostics", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overallStatus"] == "READY_FOR_GXP_PRODUCTION"
    assert data["healthScore"] == 100
    assert len(data["checks"]) == 4
    
    check_names = [c["name"] for c in data["checks"]]
    assert any("mTLS" in name for name in check_names)
    assert any("AST" in name for name in check_names)
    assert any("KMS" in name for name in check_names)


def test_cdisc_sdtm_preflight(client):
    payload = {
        "domain": "AE",
        "dataset_name": "MK-3475-Cohort-B-AdverseEvents.json"
    }
    response = client.post("/api/connect/cdisc-preflight", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["validationStatus"] == "VALIDATED_CLEAN"
    assert data["cdiscDomain"] == "AE"
    assert data["metrics"]["rawRecordsEgressed"] == 0
    assert "ZERO_CLOUD_EGRESS" in data["metrics"]["phiEgressRisk"]
    assert data["certificateId"].startswith("gxp-zkp-preflight-")


def test_dispatch_in_situ_webhook(client):
    payload = {
        "target_channel": "google_chat",
        "webhook_url": "https://chat.googleapis.com/v1/spaces/CLINICAL_TRIAL_OPS/messages",
        "trial_id": "MK-3475-087",
        "cohort": "Cohort-B",
        "proposed_dose_mg": 250.0
    }
    response = client.post("/api/connect/dispatch-webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DISPATCHED_SUCCESS"
    assert data["stateToken"].startswith("hmac-tok-")
    assert "interactiveAction" in data["a2uiCardSchema"]


def test_get_compliance_dossier(client):
    response = client.get("/api/connect/compliance-dossier")
    assert response.status_code == 200
    data = response.json()
    assert "dossierId" in data
    assert len(data["regulatoryFrameworks"]) >= 4
    assert "AMD SEV-SNP" in data["hardwareAttestation"]["enclaveType"]
    assert data["performanceBenchmark"]["astSanitizationP50Us"] <= 28.0
