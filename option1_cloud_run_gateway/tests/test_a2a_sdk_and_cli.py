import pytest
from fastapi.testclient import TestClient
from portal.app import app
from a2a_sdk.client import A2AGatewayClient

@pytest.fixture
def client(monkeypatch):
    c = A2AGatewayClient(base_url="http://testserver")
    tc = TestClient(app)

    def fake_post(path: str, payload: dict):
        resp = tc.post(path, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code} Error: {resp.text}")
        return resp.json()

    def fake_get(path: str):
        resp = tc.get(path)
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code} Error: {resp.text}")
        return resp.json()

    monkeypatch.setattr(c, "_post", fake_post)
    monkeypatch.setattr(c, "_get", fake_get)
    return c

def test_a2a_sdk_health(client):
    health = client.health()
    assert "option1" in health
    assert "option2" in health

def test_a2a_sdk_ectd_compile(client):
    res = client.compile_ectd(protocol_id="MK-3475-TEST", target_dose_mg=250.0)
    assert res["submissionId"].startswith("FDA-eCTD-IND-140288-")
    assert "verificationChecksums" in res
    assert "xmlEctdDocument" in res

def test_a2a_sdk_in_silico_simulate(client):
    res = client.simulate_in_silico(cohort_size=500, dose_mg=250.0)
    assert res["cohortSize"] == 500
    assert "pharmacodynamicResults" in res
    assert len(res["kaplanMeierSurvivalCurve"]) == 7

def test_a2a_sdk_promptcanvas_roundtrip(client):
    exported = client.export_drawio_preset("option3_dual_plane")
    assert "<mxGraphModel" in exported["xml"]
    dag = client.compile_promptcanvas_diagram(exported["xml"])
    assert dag["nodes_count"] > 0
    assert dag["edges_count"] > 0


def test_agent_teal_deployer_templates():
    from a2a_sdk.agent_teal_adapter import AgentTealGcpDeployer
    deployer = AgentTealGcpDeployer(
        agent_file="merck_oncology_agent.py",
        project_id="merck-clinical-mesh-prod",
        region="us-central1",
    )
    cb = deployer.generate_cloudbuild()
    assert "us-docker.pkg.dev/cloud-builders/docker" in cb
    assert "us-docker.pkg.dev/google.com/cloudsdktool/cloud-sdk" in cb
    assert "gcr.io" not in cb

    df = deployer.generate_dockerfile()
    assert "USER 10001:10001" in df
    assert "COPY --chown=gxpuser:gxpuser" in df

    svc = deployer.generate_service_yaml()
    assert "serving.knative.dev/v1" in svc
    assert "private-ranges-only" in svc

    card = deployer.generate_a2a_agent_card()
    assert card["protocolVersion"] == "1.0.0"
    assert card["capabilities"]["gxpSanitization"] is True
    assert card["identityFederation"]["provider"] == "Microsoft Entra ID (Azure AD)"


def test_agent_teal_gcp_deployer_scaffold(tmp_path):
    from a2a_sdk.agent_teal_adapter import AgentTealGcpDeployer
    agent_path = tmp_path / "custom_agent.py"
    agent_path.write_text("@entraId\nclass CustomAgent:\n    pass\n", encoding="utf-8")

    deployer = AgentTealGcpDeployer(str(agent_path), project_id="test-pharma", region="us-east4")
    analysis = deployer.analyze_agent()
    assert analysis["hasEntraIdDecorator"] is True
    assert "CustomAgent" in analysis["discoveredClasses"]

    artifacts = deployer.scaffold(str(tmp_path / "scaffold_out"))
    assert (tmp_path / "scaffold_out" / "Dockerfile").exists()
    assert (tmp_path / "scaffold_out" / "cloudbuild.yaml").exists()
    assert (tmp_path / "scaffold_out" / "service.yaml").exists()
    assert (tmp_path / "scaffold_out" / "agent-card.json").exists()

