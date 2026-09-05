import pytest
from a2a_sdk.client import A2AGatewayClient

def test_a2a_sdk_health():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    health = client.health()
    assert "option1" in health
    assert "option2" in health

def test_a2a_sdk_ectd_compile():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    res = client.compile_ectd(protocol_id="MK-3475-TEST", target_dose_mg=250.0)
    assert res["submissionId"].startswith("FDA-eCTD-IND-140288-")
    assert "verificationChecksums" in res
    assert "xmlEctdDocument" in res

def test_a2a_sdk_in_silico_simulate():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    res = client.simulate_in_silico(cohort_size=500, dose_mg=250.0)
    assert res["cohortSize"] == 500
    assert "pharmacodynamicResults" in res
    assert len(res["kaplanMeierSurvivalCurve"]) == 7

def test_a2a_sdk_promptcanvas_roundtrip():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    exported = client.export_drawio_preset("option3_dual_plane")
    assert "<mxGraphModel" in exported["xml"]
    dag = client.compile_promptcanvas_diagram(exported["xml"])
    assert dag["nodes_count"] > 0
    assert dag["edges_count"] > 0
