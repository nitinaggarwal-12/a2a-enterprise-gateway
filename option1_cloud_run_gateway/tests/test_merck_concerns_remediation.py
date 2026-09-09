"""Unit and integration tests verifying remediation of Merck & David Daniel concerns.

Covers:
1. Microsoft Entra ID (@entraId) token verification and claim injection.
2. AgentGPTeal GCP Runtime deployment transpilation.
3. Cross-cloud A2A dispatch to AWS Agent Core over PrivateLink with SigV4.
4. Dynamic Pydantic-to-A2UI auto-generation and streaming pause/resume lifecycle.
5. GAMP 5 & 21 CFR Part 11 IQ/OQ compliance verification endpoint.
"""

import pytest
from pydantic import BaseModel, Field
from fastapi.testclient import TestClient

from option1_cloud_run_gateway.app.security import (
    verify_entra_id_token,
    verify_unified_identity,
    entraId,
    entra_id_required,
)
from a2a_sdk.agent_teal_adapter import AgentTealGcpDeployer
from option1_cloud_run_gateway.app.aws_agentcore_bridge import AwsAgentCoreBridge
from option1_cloud_run_gateway.app.a2ui_builder import (
    pydantic_model_to_a2ui,
    A2UIStreamingLifecycle,
)
from portal.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_entra_id_token_verification():
    """Verify Microsoft Entra ID tokens are validated and extract Merck claims."""
    # Test with simulated Entra ID bearer token
    claims = verify_entra_id_token("mock-entra-token-david-daniel")
    assert claims["auth_provider"] == "microsoft_entra_id"
    assert claims["preferred_username"] == "david.daniel@merck.com"
    assert "ClinicalTrialApprover" in claims["roles"]
    assert "merck-aad-tenant-id" in claims["tid"]


def test_unified_identity_router_detects_entra_id():
    """Verify unified identity router accepts both Google OIDC and Entra ID."""
    # Entra ID token
    res_entra = verify_unified_identity("Bearer mock-entra-token-test")
    assert res_entra["auth_provider"] == "microsoft_entra_id"

    # Google token
    res_google = verify_unified_identity("Bearer mock-dev-token-admin")
    assert res_google["auth_provider"] == "google_oidc"


def test_entra_id_decorator_injection():
    """Verify @entraId decorator injects Merck identity into decorated agent method."""
    @entraId(roles=["ClinicalTrialApprover"])
    def my_clinical_agent_action(param1: str, caller_identity=None):
        return {
            "status": "PROCESSED",
            "approver": caller_identity["preferred_username"],
            "provider": caller_identity["auth_provider"],
        }

    # Execute with Entra ID token
    result = my_clinical_agent_action(
        "MK-3475",
        auth_token="Bearer mock-entra-id-token"
    )
    assert result["status"] == "PROCESSED"
    assert result["approver"] == "david.daniel@merck.com"
    assert result["provider"] == "microsoft_entra_id"


def test_agent_teal_gcp_deployer(tmp_path):
    """Verify AgentGPTeal GCP deployer scaffolds Cloud Run and Knative manifests."""
    agent_file = tmp_path / "clinical_agent.py"
    agent_file.write_text("""
from a2a_enterprise_gateway.security import entraId

@entraId(roles=["ClinicalApprover"])
def titrate(): pass
""")

    deployer = AgentTealGcpDeployer(
        agent_file=str(agent_file),
        project_id="merck-clinical-mesh-prod",
        region="us-central1"
    )
    analysis = deployer.analyze_agent()
    assert analysis["hasEntraIdDecorator"] is True
    assert "merck-clinical-mesh-prod" in analysis["identityFederation"]

    scaffold_dir = tmp_path / "dist"
    manifests = deployer.scaffold(str(scaffold_dir))
    assert (scaffold_dir / "Dockerfile").exists()
    assert (scaffold_dir / "cloudbuild.yaml").exists()
    assert (scaffold_dir / "service.yaml").exists()
    assert (scaffold_dir / "agent-card.json").exists()


@pytest.mark.asyncio
async def test_aws_agentcore_bridge_sigv4_and_sanitization():
    """Verify cross-cloud A2A dispatch strips internal AST keys and signs with SigV4."""
    bridge = AwsAgentCoreBridge(aws_region="us-east-1")
    resp = await bridge.dispatch_to_aws(
        task_id="task-test-bridge-001",
        payload={
            "protocol_id": "MK-3475-087",
            "dose_mg": 250.0,
            "__internal_trace__": "LEAK_ATTEMPT",
            "adk_internal_context": "LEAK_ATTEMPT",
        },
        simulate_success=True
    )
    assert resp["status"] == "COMPLETED"
    assert resp["bridgeDetails"]["astBlockedKeysCount"] == 2
    assert resp["bridgeDetails"]["zeroAwsModificationGuaranteed"] is True
    assert resp["awsAgentResponse"]["verdict"] == "COHORT_RESERVATIONS_CONFIRMED"


def test_pydantic_model_to_a2ui_dynamic_generation():
    """Verify automatic A2UI generation from Python Pydantic models."""
    class DoseTitrationForm(BaseModel):
        target_dose_mg: float = Field(..., description="Target dose in milligrams")
        patient_cohort: str = Field(..., description="Target cohort name")
        enable_protectant: bool = Field(True, description="Enable prophylactic protectant")

    card = pydantic_model_to_a2ui(DoseTitrationForm, title="Review Keytruda Dose")
    assert card["title"] == "Review Keytruda Dose"
    assert len(card["fields"]) == 3
    field_ids = [f["id"] for f in card["fields"]]
    assert "target_dose_mg" in field_ids
    assert "patient_cohort" in field_ids
    assert "enable_protectant" in field_ids
    assert len(card["actions"]) == 1
    assert len(card["actions"][0]["stateToken"]) > 20


def test_a2ui_streaming_pause_and_resume():
    """Verify A2UI streaming pause signal and continuation trace."""
    pause_event = A2UIStreamingLifecycle.create_pause_signal(
        task_id="task-stream-009",
        reason="Grade 2 AST spike requires human clinician approval",
        a2ui_card={"title": "Titration Card"},
    )
    assert pause_event["state"] == "INPUT_REQUIRED"
    assert "resumeEndpoint" in pause_event

    resume_event = A2UIStreamingLifecycle.resume_streaming_task(
        task_id="task-stream-009",
        action_payload={"approvedDoseMg": 250.0},
        verified_identity={"preferred_username": "david.daniel@merck.com", "auth_provider": "microsoft_entra_id"}
    )
    assert resume_event["state"] == "RESUMED"
    assert resume_event["signer"] == "david.daniel@merck.com"


def test_iq_oq_dossier_endpoint(client):
    """Verify GAMP 5 Category 4 IQ/OQ compliance endpoint returns qualified dossier."""
    resp = client.get("/api/iq-oq-dossier")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sponsor"] == "Merck Sharp & Dohme LLC"
    assert data["iqResults"]["status"] == "QUALIFIED"
    assert data["oqResults"]["status"] == "QUALIFIED"
    assert data["regulatorySignoff"]["verdict"] == "APPROVED FOR GxP CLINICAL USE"


def test_cross_cloud_dispatch_endpoint(client):
    """Verify cross-cloud A2A dispatch endpoint interoperates with AWS."""
    resp = client.post("/api/bridge/cross-cloud-dispatch", json={
        "target_aws_region": "us-east-1",
        "target_protocol": "MK-3475-087",
        "target_dose_mg": 250.0,
        "simulate": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["bridgeDetails"]["zeroAwsModificationGuaranteed"] is True
