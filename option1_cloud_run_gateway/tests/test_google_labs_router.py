"""
Test Suite for Google Labs & DeepMind Foundational Models in Biopharma Gateway
Endpoints tested:
1. GET /api/google-labs/alphafold-docking
2. POST /api/google-labs/translate
3. POST /api/google-labs/transcribe-attestation
4. POST /api/google-labs/pharmacovigilance-radar
5. GET /api/google-labs/fda-inspection-dossier
"""

import pytest
from fastapi.testclient import TestClient
from portal.app import app

client = TestClient(app)

def test_alphafold_docking_endpoint():
    resp = client.get("/api/google-labs/alphafold-docking?dose_mg=300")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "google-deepmind/alphafold-3"
    assert data["targetReceptor"]["gene"] == "PDCD1"
    assert data["dockingKinetics"]["dissociationConstantKdNm"] == 0.28
    assert data["dockingKinetics"]["receptorOccupancyPct"] > 80.0
    assert "offTargetSafetyProfile" in data
    assert data["offTargetSafetyProfile"]["status"] == "PASS_CLEARED_GXP"
    assert len(data["keyBindingResidues"]) >= 4
    assert data["latencyMs"] < 50.0

def test_translate_regulatory_dossier_japanese_pmda():
    payload = {
        "text": "Titrate Cohort-B dosage to mitigate Grade 1 ALT elevation while maintaining target receptor occupancy.",
        "source_lang": "en",
        "target_lang": "ja",
        "regulatory_agency": "PMDA"
    }
    resp = client.post("/api/google-labs/translate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["targetLanguage"] == "ja"
    assert "PMDA" in data["targetAgency"]
    assert "承認" in data["translatedTitle"]
    assert data["cryptographicBindingHash"].startswith("sha256:")
    assert data["meddraTerminologyMatched"] is True

def test_translate_regulatory_dossier_german_bfarm():
    payload = {
        "text": "Titrate Cohort-B dosage to mitigate Grade 1 ALT elevation while maintaining target receptor occupancy.",
        "source_lang": "en",
        "target_lang": "de",
        "regulatory_agency": "BfArM"
    }
    resp = client.post("/api/google-labs/translate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["targetLanguage"] == "de"
    assert "BfArM" in data["targetAgency"]
    assert "Genehmigung" in data["translatedTitle"]

def test_transcribe_verbal_attestation_chirp2():
    payload = {
        "investigator_name": "Dr. Eleanor Vance, MD",
        "study_id": "MK-3475-087",
        "cohort": "Cohort-B",
        "approved_dose_mg": 250.0
    }
    resp = client.post("/api/google-labs/transcribe-attestation", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "fullTranscript" in data
    assert "Dr. Eleanor Vance, MD" in data["fullTranscript"]
    assert len(data["wordLevelTimestamps"]) > 0
    assert data["regulatoryAttestation"]["statutoryStatus"] == "LEGALLY_BINDING_VERBAL_SIGNATURE"
    assert data["meanConfidence"] >= 0.95

def test_pharmacovigilance_radar_gemini_flash():
    payload = {
        "narrative": "Subject 087-014 experienced bilateral upper extremity paresthesia, mild jaundice, and elevated serum transaminases 4 days post 300mg infusion.",
        "study_id": "MK-3475-087",
        "dose_mg": 300.0
    }
    resp = client.post("/api/google-labs/pharmacovigilance-radar", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "gemini-2.5-flash-preview"
    assert data["varianceTriggered"] is True
    assert len(data["extractedAdverseEvents"]) >= 3
    pts = [e["meddraPt"] for e in data["extractedAdverseEvents"]]
    assert "Alanine aminotransferase increased" in pts
    assert "Jaundice" in pts
    assert data["semanticFirewall"]["phiPiiDeIdentified"] is True

def test_fda_inspection_dossier_gemini_pro():
    resp = client.get("/api/google-labs/fda-inspection-dossier")
    assert resp.status_code == 200
    data = resp.json()
    assert data["generatorModel"] == "gemini-2.5-pro"
    assert data["inspectionId"] == "FDA-AUDIT-2026-A2A-09881"
    assert data["merkleRootSha256"].startswith("sha256:")
    assert data["pinnacle21Validation"]["status"] == "CONFORMANT_READY_FOR_BLA"


def test_deepmind_tts_matrix_endpoint():
    resp = client.get("/api/google-labs/tts/matrix")
    assert resp.status_code == 200
    data = resp.json()
    assert "gemini-2.5-flash-preview-tts" in data["supportedModels"]
    assert "gemini-3.1-flash-tts-preview" in data["supportedModels"]
    assert "Charon" in data["baseVoices"]
    assert "Aoede" in data["baseVoices"]
    assert "Fenrir" in data["baseVoices"]
    assert "Puck" in data["baseVoices"]
    assert "architect" in data["personas"]
    assert "clinician" in data["personas"]
    assert "compliance" in data["personas"]
    assert "developer" in data["personas"]
    assert len(data["accents"]) >= 5
    assert len(data["emotionalModes"]) >= 3


def test_deepmind_tts_synthesize_all_personas():
    for persona, voice, model in [
        ("architect", "Charon", "gemini-2.5-flash-preview-tts"),
        ("clinician", "Aoede", "gemini-3.1-flash-tts-preview"),
        ("compliance", "Fenrir", "gemini-2.5-flash-preview-tts"),
        ("developer", "Puck", "gemini-3.1-flash-tts-preview"),
    ]:
        payload = {
            "step": 2,
            "persona": persona,
            "model": model,
            "voice_name": voice,
            "emotional_mode": "clinical_precision",
            "accent": "us_silicon_valley"
        }
        resp = client.post("/api/google-labs/tts/synthesize", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"] == model
        assert data["persona"] == persona
        assert data["voice"]["name"] == voice
        assert data["audioUrl"].endswith(".m4a")
        assert len(data["wordTimings"]) > 0
        assert data["wordTimings"][0]["word"].startswith("Step")
        assert data["cryptographicBinding"]["sha256"].startswith("sha256:")
        assert data["dspWarmthProfile"]["karaokeGlowColor"] == "#fbbf24"


def test_deepmind_prompt_to_voice_designer():
    payload = {
        "prompt": "Warm British senior oncologist explaining therapy with calm bedside empathy",
        "archetype": "research_professor"
    }
    resp = client.post("/api/google-labs/tts/design-voice", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["designedVoice"]["baseVoice"] == "Aoede"
    assert data["designedVoice"]["accent"] == "uk_rp"
    assert data["designedVoice"]["shareablePersonaToken"].startswith("VOICE-VAULT-")
    assert "formantConvolver" in data
    assert data["formantConvolver"]["F1_Warmth"] == 520

