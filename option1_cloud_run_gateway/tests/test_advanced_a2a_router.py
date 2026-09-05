"""Unit & Integration tests for Advanced A2A Protocol Lab Router.

Tests all 6 core pillars:
1. A2A <-> MCP Bi-directional Bridge (Tools Manifest & Execute)
2. Byzantine Quorum Swarm Voting & Red/Blue Team Debate
3. Sequential 3-Tier 21 CFR Part 11 Multi-Sig Electronic Signature Chain
4. In-Flight Streaming Steering & AIP-127 Durable Checkpoint/Resumption
5. Confidential AMD SEV-SNP Enclave Attestation & Zero-Knowledge Cohort Proofs
6. W3C OpenTelemetry Distributed Trace Waterfall & Adaptive Chaos Simulator
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
# 1. A2A <-> MCP Protocol Bridge Tests
# ----------------------------------------------------------------------------

def test_mcp_tools_manifest(client):
    response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) >= 3
    tool_names = [t["name"] for t in data["tools"]]
    assert "titrate_clinical_dose" in tool_names
    assert "verify_21cfr11_multisig" in tool_names
    assert "ingest_cdisc_sdtm_domain" in tool_names
    assert data["bridge_protocol"] == "A2A_MCP_CONVERTER_V1"
    assert data["supported_a2a_version"] == "1.0.0"


def test_mcp_convert_and_execute(client):
    payload = {
        "client_type": "claude_mcp",
        "tool_name": "titrate_clinical_dose",
        "arguments": {
            "study_id": "MK-3475-087",
            "cohort": "Cohort-B",
            "target_dose_mg": 275.0,
            "justification": "Mitigate Grade 1 ALT elevation while maintaining target receptor occupancy."
        }
    }
    response = client.post("/api/mcp/convert-and-execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Verify MCP translation to A2A AIP-127 Task
    translated = data["translatedA2APayload"]
    assert translated["jsonrpc"] == "2.0"
    assert translated["method"] == "a2a.tasks.execute"
    assert translated["params"]["targetAgent"] == "dr-a2a-clinical-gateway"
    assert translated["params"]["parameters"]["target_dose_mg"] == 275.0
    
    # Verify MCP standard response returned
    mcp_resp = data["mcpResponse"]
    assert mcp_resp["isError"] is False
    assert len(mcp_resp["content"]) > 0
    assert "Successfully executed clinical tool" in mcp_resp["content"][0]["text"]
    assert data["bridgeStats"]["transportStatus"] == "HTTP_200_SUCCESS"


# ----------------------------------------------------------------------------
# 2. Byzantine Quorum Voting & Red/Blue Debate Tests
# ----------------------------------------------------------------------------

def test_quorum_evaluate_majority_and_unanimous(client):
    # Test 1: Moderate dose (300mg) under majority rule -> should pass 3/3 or 2/3
    res1 = client.post("/api/quorum/evaluate", json={
        "amendment_id": "AMD-ONC-2026-08",
        "proposed_dose_mg": 280.0,
        "quorum_rule": "majority"
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["quorumReached"] is True
    assert data1["consensusStamp"] == "CONSENSUS_APPROVED"
    assert len(data1["votes"]) == 3
    assert len(data1["debateTranscript"]) >= 3

    # Test 2: High dose (380mg) under unanimous rule -> should fail (FDA/EMA reject)
    res2 = client.post("/api/quorum/evaluate", json={
        "amendment_id": "AMD-ONC-2026-09",
        "proposed_dose_mg": 380.0,
        "quorum_rule": "unanimous"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["quorumReached"] is False
    assert data2["consensusStamp"] == "CONSENSUS_REJECTED"
    assert data2["tally"]["reject"] >= 1


# ----------------------------------------------------------------------------
# 3. Sequential 3-Tier 21 CFR Part 11 Multi-Sig Chain Tests
# ----------------------------------------------------------------------------

def test_multisig_sign_tier_chain(client):
    cert_id = "MK-SIG-2026-881"
    amendment = {"protocol": "MK-3475", "delta": "+25mg"}

    # Tier 1
    t1 = client.post("/api/multisig/sign-tier", json={
        "certificate_id": cert_id,
        "tier": 1,
        "signer_name": "Dr. Sarah Chen, MD",
        "signer_role": "Principal Investigator (Site 104)",
        "meaning": "I have evaluated the participant safety profile and approve titration.",
        "previous_hash": None,
        "amendment_data": amendment
    })
    assert t1.status_code == 200
    d1 = t1.json()
    assert d1["tier"] == 1
    assert d1["isFinalTier"] is False
    assert d1["kmsSignature"].startswith("kms-ed25519-")
    hash_t1 = d1["currentHash"]

    # Tier 2 chained to Tier 1
    t2 = client.post("/api/multisig/sign-tier", json={
        "certificate_id": cert_id,
        "tier": 2,
        "signer_name": "Marcus Vance, PhD",
        "signer_role": "Lead Clinical Biostatistician",
        "meaning": "Statistical power verified at 94.2% across Bayesian safety endpoints.",
        "previous_hash": hash_t1,
        "amendment_data": amendment
    })
    assert t2.status_code == 200
    d2 = t2.json()
    assert d2["tier"] == 2
    assert d2["previousHash"] == hash_t1
    assert d2["isFinalTier"] is False
    hash_t2 = d2["currentHash"]

    # Tier 3 chained to Tier 2 (Final)
    t3 = client.post("/api/multisig/sign-tier", json={
        "certificate_id": cert_id,
        "tier": 3,
        "signer_name": "Dr. Elena Rostova, MD, PhD",
        "signer_role": "Global Medical Review Director",
        "meaning": "Final executive regulatory sign-off for protocol amendment execution.",
        "previous_hash": hash_t2,
        "amendment_data": amendment
    })
    assert t3.status_code == 200
    d3 = t3.json()
    assert d3["tier"] == 3
    assert d3["previousHash"] == hash_t2
    assert d3["isFinalTier"] is True
    assert d3["status"] == "CHAINED_VALID"


# ----------------------------------------------------------------------------
# 4. In-Flight Streaming & AIP-127 Checkpoint Tests
# ----------------------------------------------------------------------------

def test_streaming_steer(client):
    res = client.post("/api/streaming/steer", json={
        "task_id": "a2a-stream-9921",
        "steering_prompt": "Prioritize Grade 3 ALT safety over speed.",
        "target_constraint": "ALT_TOXICITY_CEILING_STRICT"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "STEER_INJECTED"
    assert data["taskId"] == "a2a-stream-9921"
    assert "ALT_TOXICITY_CEILING_STRICT" in data["activeAdjustment"]


def test_streaming_checkpoint_and_resume(client):
    # Snapshot
    snap_res = client.post("/api/streaming/checkpoint", json={
        "task_id": "a2a-lro-5501",
        "action": "snapshot"
    })
    assert snap_res.status_code == 200
    snap_data = snap_res.json()
    assert snap_data["status"] == "CHECKPOINT_CREATED"
    assert snap_data["checkpointToken"].startswith("chkpt-aip127-")
    token = snap_data["checkpointToken"]

    # Resume
    resume_res = client.post("/api/streaming/checkpoint", json={
        "task_id": "a2a-lro-5501",
        "action": "resume",
        "checkpoint_token": token
    })
    assert resume_res.status_code == 200
    resume_data = resume_res.json()
    assert resume_data["status"] == "EXECUTION_RESUMED"
    assert resume_data["resumedFromStep"] == 5


# ----------------------------------------------------------------------------
# 5. AMD SEV-SNP Enclave Attestation & ZKP Tests
# ----------------------------------------------------------------------------

def test_enclave_attestation_report(client):
    res = client.get("/api/enclave/attestation-report")
    assert res.status_code == 200
    data = res.json()
    assert data["attestationStatus"] == "VERIFIED_HARDWARE_ENCLAVE"
    assert "AMD SEV-SNP" in data["platform"]
    assert "pcr0" in data["hardwareReport"]
    assert data["zeroHostAccess"] is True


def test_enclave_zkp_verify(client):
    res = client.post("/api/enclave/verify-zkp", json={
        "cohort_size": 420,
        "min_age_threshold": 18,
        "max_bilirubin_mg_dl": 1.5
    })
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is True
    assert data["proofType"] == "Groth16_zkSNARK"
    assert data["phiEgressDetected"] is False
    assert data["rawRecordsTransmitted"] == 0
    assert data["publicInputs"]["patientCountSatisfied"] == 420


# ----------------------------------------------------------------------------
# 6. W3C Trace Waterfall & Chaos Resilience Tests
# ----------------------------------------------------------------------------

def test_telemetry_distributed_trace(client):
    res = client.get("/api/telemetry/distributed-trace")
    assert res.status_code == 200
    data = res.json()
    assert "traceId" in data
    assert data["w3cTraceparent"].startswith("00-")
    assert len(data["spans"]) == 5
    assert data["hopCount"] == 5
    assert "totalMeshDurationMs" in data


def test_chaos_simulate(client):
    # 503 fault -> Circuit breaker OPEN
    res_503 = client.post("/api/chaos/simulate", json={
        "injection_type": "subagent_503",
        "severity": 80
    })
    assert res_503.status_code == 200
    d_503 = res_503.json()
    assert "OPEN" in d_503["circuitBreakerState"]
    assert d_503["deadLetterQueue"]["queued"] is True

    # 429 fault -> HALF-OPEN
    res_429 = client.post("/api/chaos/simulate", json={
        "injection_type": "rate_limit_429",
        "severity": 60
    })
    assert res_429.status_code == 200
    d_429 = res_429.json()
    assert "HALF-OPEN" in d_429["circuitBreakerState"]
    assert d_429["deadLetterQueue"]["queued"] is True

    # Normal jitter -> CLOSED
    res_jitter = client.post("/api/chaos/simulate", json={
        "injection_type": "jitter",
        "severity": 20
    })
    assert res_jitter.status_code == 200
    d_jitter = res_jitter.json()
    assert "CLOSED" in d_jitter["circuitBreakerState"]
    assert d_jitter["deadLetterQueue"]["queued"] is False
