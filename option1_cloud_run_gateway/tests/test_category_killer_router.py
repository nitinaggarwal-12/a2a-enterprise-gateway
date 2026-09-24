"""Unit & Integration tests for Flagship Category-Defining Capabilities Router.

Tests both breakthrough pillars:
1. 1-Click FDA eCTD 3.2.2 Automated Regulatory Dossier Compiler
2. In-Silico 10,000 Digital Twin Patient Clinical Trial Simulator
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


# ----------------------------------------------------------------------------
# 1. FDA eCTD 3.2.2 Compiler Tests
# ----------------------------------------------------------------------------

def test_compile_fda_ectd_dossier(client):
    payload = {
        "protocol_id": "MK-3475-087",
        "amendment_id": "AMD-ONC-2026-08",
        "multisig_certificate_id": "MK-SIG-2026-881",
        "target_dose_mg": 250.0,
        "justification": "Mitigate Grade 1 ALT elevation while maintaining 88.4% target receptor occupancy.",
        "sponsor_name": "Merck Sharp & Dohme LLC",
        "indication": "Non-Small Cell Lung Carcinoma (NSCLC) Cohort-B"
    }
    response = client.post("/api/ectd/compile", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "eCTD_BUNDLE_COMPILED_READY_FOR_ESG"
    assert "FDA-eCTD-IND-140288" in data["submissionId"]
    assert data["form1571"]["indNumber"] == "IND-140288"
    assert data["form1572"]["principalInvestigator"] == "Dr. Sarah Chen, MD (Site 104)"
    
    # Verify Merkle Tree Chaining
    merkle = data["merkleAuditTrail"]
    assert merkle["chainVerification"] == "VALID_TAMPER_EVIDENT"
    assert len(merkle["tiers"]) == 3
    assert merkle["tiers"][0]["role"] == "Principal Investigator"
    assert merkle["tiers"][1]["role"] == "Lead Biostatistician"
    assert merkle["tiers"][2]["role"] == "Medical Review Director"
    
    # Verify XML DTD 3.2.2 Compliance
    assert 'SYSTEM "util/dtd/ich-ectd-3-2-2.dtd"' in data["xmlEctdDocument"]
    assert "<m2-5-clinical-overview>" in data["xmlEctdDocument"]
    assert len(data["verificationChecksums"]["sha256"]) == 64


# ----------------------------------------------------------------------------
# 2. In-Silico 10,000 Digital Twin Simulator Tests
# ----------------------------------------------------------------------------

def test_in_silico_trial_simulation_standard(client):
    payload = {
        "cohort_size": 10000,
        "target_dose_mg": 250.0,
        "trial_duration_weeks": 24,
        "prophylactic_hepatic_protectant": True,
        "base_population": "advanced_nsclc_second_line"
    }
    response = client.post("/api/insilico/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["cohortSize"] == 10000
    assert data["targetDoseMg"] == 250.0
    assert data["safetyVerdict"] == "MTD_APPROVED_FOR_CLINICAL_ESCALATION"
    assert "SIM-TWIN-" in data["simulationId"]
    
    # Verify Kaplan-Meier Curve
    curve = data["kaplanMeierSurvivalCurve"]
    assert len(curve) == 7
    assert curve[0]["week"] == 0
    assert curve[0]["survivalProbability"] == 100.0
    assert curve[-1]["week"] == 24
    assert curve[-1]["activeCohortCount"] > 5000
    
    # Verify Pharmacodynamics
    pd = data["pharmacodynamicResults"]
    assert "projectedEfficacyRate" in pd
    assert "grade3_4Toxicity" in pd
    assert data["virtualTwinSwarmSummary"]["totalSyntheticPatients"] == 10000


def test_in_silico_trial_simulation_high_dose_unprotected(client):
    # High dose without hepatic protectant -> should increase toxicity
    payload = {
        "cohort_size": 5000,
        "target_dose_mg": 380.0,
        "trial_duration_weeks": 24,
        "prophylactic_hepatic_protectant": False,
        "base_population": "advanced_nsclc_second_line"
    }
    response = client.post("/api/insilico/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["targetDoseMg"] == 380.0
    assert data["prophylacticProtectantActive"] is False
