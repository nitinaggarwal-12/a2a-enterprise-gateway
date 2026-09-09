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
