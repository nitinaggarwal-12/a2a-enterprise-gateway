import pytest
from fastapi.testclient import TestClient
from portal.app import app
from portal.promptcanvas_bridge_router import ARCHETYPE_XML_TEMPLATES

client = TestClient(app)

def test_promptcanvas_get_diagram_templates():
    response = client.get("/api/promptcanvas/diagrams")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["templates"]) >= 2
    keys = [t["key"] for t in data["templates"]]
    assert "option3_dual_plane" in keys
    assert "option1_cloud_run" in keys

def test_promptcanvas_get_diagram_by_key():
    response = client.get("/api/promptcanvas/diagram/option3_dual_plane")
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "option3_dual_plane"
    assert "mxGraphModel" in data["drawioXml"]

def test_promptcanvas_compile_to_dag_valid():
    sample_xml = ARCHETYPE_XML_TEMPLATES["option3_dual_plane"]["xml"]
    response = client.post("/api/promptcanvas/compile-to-dag", json={
        "drawio_xml": sample_xml,
        "target_protocol": "a2a.v1.0.0",
        "enforce_ast_sanitization": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["dag_id"].startswith("DAG-PROMPTCANVAS-")
    assert data["nodes_count"] >= 10
    assert data["edges_count"] >= 8
    assert data["gxp_21cfr11_compliant"] is True
    assert len(data["execution_plan"]) == data["nodes_count"]

def test_promptcanvas_export_xml():
    response = client.post("/api/promptcanvas/export-xml", json={
        "architecture_preset": "option1_cloud_run"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "A2A_Gateway_option1_cloud_run.drawio"
    assert "<mxGraphModel" in data["xml"]

def test_promptcanvas_compile_invalid_xml():
    response = client.post("/api/promptcanvas/compile-to-dag", json={
        "drawio_xml": "<invalid>No graph</invalid>",
        "target_protocol": "a2a.v1.0.0"
    })
    assert response.status_code == 400
