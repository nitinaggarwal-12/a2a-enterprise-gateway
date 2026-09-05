"""
Test Suite for Google Gemini Omni UI/UX Navigation Orchestrator & User Readiness Engine
Endpoints tested:
1. POST /api/omni/orchestrate (Voice Query & Context Resolution)
2. GET /api/omni/user-readiness (21 CFR Part 11 Readiness Score)
3. POST /api/omni/design-mutation (Dynamic CSS Grid Morphing)
"""

import pytest
from fastapi.testclient import TestClient
from portal.app import app

client = TestClient(app)

def test_get_user_readiness_baseline():
    resp = client.get("/api/omni/user-readiness?dose_mg=300&has_signed=false&pv_cleared=true&tab=dose_curve")
    assert resp.status_code == 200
    data = resp.json()
    assert "overallReadinessPct" in data
    assert 60 <= data["overallReadinessPct"] <= 100
    assert "readinessTier" in data
    assert len(data["dimensions"]) == 4
    dim_names = [d["name"] for d in data["dimensions"]]
    assert "Protocol Regimen Alignment" in dim_names
    assert "AlphaFold 3 Receptor Kinetics" in dim_names
    assert "Gemini Flash Pharmacovigilance" in dim_names
    assert "21 CFR § 11.50 Electronic Attestation" in dim_names

def test_omni_orchestrate_split_focus_voice_query():
    payload = {
        "current_tab": "landing",
        "active_persona": "clinician",
        "voice_query": "Omni, show me binding affinity vs liver risk in split view",
        "dose_mg": 300.0,
        "has_signed": False,
        "pv_cleared": True
    }
    resp = client.post("/api/omni/orchestrate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "MORPH_LAYOUT"
    assert data["layoutMode"] == "split_focus"
    assert data["targetTab"] == "dose_curve"
    assert data["spotlightSelector"] == "#alphafold-3d-viewport"
    assert "AlphaFold 3" in data["spokenNarration"]
    assert len(data["suggestedActions"]) > 0

def test_omni_orchestrate_pmda_regulatory_query():
    payload = {
        "current_tab": "dose_curve",
        "active_persona": "compliance",
        "voice_query": "Prepare protocol rationale for Japan PMDA submission",
        "dose_mg": 250.0,
        "has_signed": False,
        "pv_cleared": True
    }
    resp = client.post("/api/omni/orchestrate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "SET_LANGUAGE"
    assert "PMDA" in data["spokenNarration"]
    assert "JTI" in data["spokenNarration"]

def test_omni_orchestrate_fda_dossier_query():
    payload = {
        "current_tab": "landing",
        "active_persona": "architect",
        "voice_query": "Compile 1-click FDA inspection audit dossier",
        "dose_mg": 300.0,
        "has_signed": True,
        "pv_cleared": True
    }
    resp = client.post("/api/omni/orchestrate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "OPEN_FDA_DOSSIER"
    assert data["spotlightSelector"] == "#modal-fda-dossier"
    assert "Merkle root" in data["spokenNarration"]

def test_omni_orchestrate_electronic_signature_query():
    payload = {
        "current_tab": "dose_curve",
        "active_persona": "clinician",
        "voice_query": "I am ready to sign and attest this dose",
        "dose_mg": 250.0,
        "has_signed": False,
        "pv_cleared": True
    }
    resp = client.post("/api/omni/orchestrate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "OPEN_SIGNATURE"
    assert data["spotlightSelector"] == "#modal-justification"
    assert "Chirp 2" in data["spokenNarration"]

def test_design_mutation_adaptive_layout():
    for mode in ["standard", "split_focus", "high_density", "guided_step"]:
        payload = {
            "layout_mode": mode,
            "cognitive_load_index": 0.75,
            "active_persona": "clinician"
        }
        resp = client.post("/api/omni/design-mutation", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["layoutMode"] == mode
        assert "gridTemplate" in data["mutation"]
        assert data["cognitiveLoadAdaptiveAdjustments"]["hideTelemetryHex"] is True
