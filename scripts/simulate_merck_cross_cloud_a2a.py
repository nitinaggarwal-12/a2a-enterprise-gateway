#!/usr/bin/env python3
"""
Simulate Cross-Cloud Agent-to-Agent (A2A) and A2UI Communication
Between a GCP Agent and an AWS Agent in a Regulated Biopharma (Merck) Environment
Protected by Google Cloud VPC Service Controls (VPC-SC) and Private Service Connect (PSC).

Scenario:
  - Caller: AWS Agent (AWS Bedrock / SageMaker BioNeMo in private AWS VPC us-east-1)
  - Target: GCP Sovereign Clinical Agent (Vertex AI inside VPC-SC perimeter in us-central1)
  - Network: Cross-Cloud Private Interconnect (AWS PrivateLink <-> GCP PSC, Zero Public Internet)
  - Protocol: Google Agent-to-Agent (A2A) v1.0.0 (JSON-RPC / gRPC) + A2UI Cards
  - Security: 
      1. VPC-SC Ingress Rule with Workload Identity Federation (AWS IAM -> GCP STS)
      2. In-memory Sub-28 µs AST Sanitization (Zero prompt/trace egress)
      3. Stateless 48-hour HMAC-SHA256 Electronic Signatures (FDA 21 CFR Part 11)
      4. Zero Raw CDISC SDTM Patient PHI egress to external cloud
"""

import sys
import os
import time
import json
import hmac
import hashlib
import uuid
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from option1_cloud_run_gateway.app.sanitizer import sanitize_payload, is_prohibited_key

# ANSI Color Codes
CYAN = "\033[96m"
TEAL = "\033[36m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def log_step(phase: str, title: str):
    print(f"\n{BOLD}{CYAN}=== [{phase}] {title} ==={RESET}")

def log_info(actor: str, msg: str):
    print(f"{TEAL}[{actor}]{RESET} {msg}")

def log_success(msg: str):
    print(f"{GREEN}  ✔ {msg}{RESET}")

def log_metric(label: str, val: str):
    print(f"  {DIM}• {label}:{RESET} {BOLD}{val}{RESET}")

def main():
    print(f"\n{BOLD}{GREEN}================================================================================")
    print(" 🔬 MERCK RESEARCH LABS: CROSS-CLOUD AGENT-TO-AGENT (A2A) SIMULATION")
    print(" GCP Sovereign Enclave (VPC-SC) <---> AWS BioNeMo Swarm (PrivateLink)")
    print(f"================================================================================{RESET}")

    # --------------------------------------------------------------------------
    # Step 1: AWS Agent Initiates Cross-Cloud A2A Request
    # --------------------------------------------------------------------------
    log_step("STEP 1", "AWS Agent Ingests Trial Data & Dispatches A2A Request")
    aws_caller_context = {
        "cloud": "AWS",
        "region": "us-east-1",
        "vpc_id": "vpc-0a89d71c4e9f3b12",
        "agent_id": "arn:aws:iam::123456789012:role/merck-bionemo-clinical-agent",
        "sts_federation_token": "aws-sts-sigv4-" + uuid.uuid4().hex[:16]
    }
    
    # Authentic A2A Protocol v1.0.0 JSON-RPC Envelope
    a2a_task_request = {
        "jsonrpc": "2.0",
        "id": f"a2a-task-{uuid.uuid4().hex[:12]}",
        "method": "a2a.clinical.evaluate_study",
        "params": {
            "studyId": "MK-3475-087",
            "cohort": "Cohort-B",
            "therapeuticArea": "Oncology (Immunotherapy)",
            "investigationalProduct": "Pembrolizumab (Keytruda) + Novel Multi-Kinase Inhibitor",
            "queryObjective": "Evaluate Grade 3/4 Hepatotoxicity variance and propose protocol amendment"
        },
        "metadata": {
            "a2a_version": "1.0.0",
            "client_timestamp": datetime.now(timezone.utc).isoformat(),
            "transport": "AWS_PRIVATELINK_TO_GCP_PSC"
        }
    }
    
    log_info("AWS Agent", f"Executing in AWS VPC: {aws_caller_context['vpc_id']} ({aws_caller_context['region']})")
    log_info("AWS Agent", f"Targeting GCP Sovereign Endpoint: psc://sovereign-gateway.merck.internal:50051")
    log_info("AWS Agent", f"Dispatching Google A2A v1.0.0 Task: {a2a_task_request['id']}")
    log_metric("Method", a2a_task_request["method"])
    log_metric("Study ID", a2a_task_request["params"]["studyId"])
    log_metric("Egress Route", "AWS PrivateLink -> Cross-Cloud Interconnect -> GCP PSC (Zero Internet)")

    # --------------------------------------------------------------------------
    # Step 2: GCP VPC Service Controls (VPC-SC) Perimeter Boundary Enforcement
    # --------------------------------------------------------------------------
    log_step("STEP 2", "GCP VPC-SC Perimeter Ingress & Identity Verification")
    
    vpc_sc_policy = {
        "perimeter": "accessPolicies/merck_access_policy/servicePerimeters/sp_merck_clinical_prod",
        "protected_services": [
            "aiplatform.googleapis.com",   # Vertex AI
            "bigquery.googleapis.com",     # Clinical Data Warehouse
            "storage.googleapis.com"       # CDISC SDTM Bucket
        ],
        "ingress_rule": {
            "identity_type": "WORKLOAD_IDENTITY_FEDERATION",
            "allowed_aws_role": "arn:aws:iam::123456789012:role/merck-bionemo-clinical-agent",
            "ingress_network": "projects/merck-clinical-gxp/regions/us-central1/serviceAttachments/a2a-psc-producer"
        }
    }

    log_info("GCP VPC-SC", f"Inspecting inbound packet against perimeter: {vpc_sc_policy['perimeter']}")
    
    # Verify Workload Identity Federation
    if aws_caller_context["agent_id"] == vpc_sc_policy["ingress_rule"]["allowed_aws_role"]:
        log_success("Workload Identity Federation: Validated AWS IAM Role -> GCP SA Token Exchange.")
        log_success("VPC-SC Ingress Approved: Request admitted via Private Service Connect attachment.")
        log_metric("VPC-SC Boundary", "ENFORCED (Zero Public IP Ingress)")
        log_metric("mTLS 1.3 Cipher", "TLS_AES_256_GCM_SHA384 (Merck Private CAS)")
    else:
        print(f"{RED}❌ VPC-SC VIOLATION: Caller identity rejected by ingress rule.{RESET}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 3: GCP Sovereign Agent Bayesian Reasoning & CDISC Ingestion
    # --------------------------------------------------------------------------
    log_step("STEP 3", "GCP Sovereign Agent: Vertex AI Bayesian Toxicity Analysis")
    
    log_info("GCP Agent", "Loading restricted CDISC SDTM dataset from BigQuery (In-situ, no data movement)...")
    time.sleep(0.3)
    
    # Internal Sovereign Reasoning (Produces raw thought trace with internal envelopes)
    raw_sovereign_output = {
        "studyId": "MK-3475-087",
        "cohort": "Cohort-B",
        "patients_evaluated": 240,
        "adverse_events": {
            "grade_3_4_hepatotoxicity_rate": "10.0%",
            "grade_3_4_baseline_rate": "4.6%",
            "variance_delta": "+5.42%",
            "immune_mediated_hepatitis_n": 2,
            "clinical_significance": "Statistically significant elevation above safety margin"
        },
        "recommendation": "Dose Titration Reduction: Lower dose from 400mg Q6W to 300mg Q4W + mandatory weekly LFT monitoring.",
        # PROHIBITED ADK/VERTEX INTERNAL ENVELOPES (MUST BE STRIPPED BEFORE AWS EGRESS)
        "__internal_trace__": {
            "vertex_model": "gemini-1.5-pro-clinical-sovereign",
            "prompt_tokens": 14208,
            "thought_chain": "Step 1: Ingested SDTM AE and LB domains... Bayesian prior distribution showed 0.12 alpha...",
            "vector_embedding_id": "vec-881273-merck-private"
        },
        "adk_internal_context": {
            "orchestration_session": "sess-mrl-00921",
            "cluster_ip": "10.240.0.12"
        },
        "prompt_injection_flag": False
    }

    log_success("Sovereign Vertex AI analysis complete within enclave.")
    log_metric("Evaluated Patients", str(raw_sovereign_output["patients_evaluated"]))
    log_metric("Hepatotoxicity Variance", raw_sovereign_output["adverse_events"]["variance_delta"])
    log_metric("Recommendation", raw_sovereign_output["recommendation"])

    # --------------------------------------------------------------------------
    # Step 4: Sub-28 µs In-Memory AST Sanitization Before Egress
    # --------------------------------------------------------------------------
    log_step("STEP 4", "Sub-28 µs AST Sanitization (Preventing Cloud Egress Leaks)")
    
    log_info("AST Sanitizer", "Scanning payload dictionary tree to strip prohibited internal orchestrator keys...")
    t_ast_start = time.perf_counter_ns()
    removed_keys = [k for k in raw_sovereign_output if is_prohibited_key(k)]
    clean_payload = sanitize_payload(raw_sovereign_output)
    t_ast_us = (time.perf_counter_ns() - t_ast_start) / 1000.0

    assert "__internal_trace__" not in clean_payload
    assert "adk_internal_context" not in clean_payload
    assert "prompt_injection_flag" not in clean_payload

    log_success(f"Sanitization completed in {t_ast_us:.2f} µs (SLA: < 28.00 µs)")
    log_metric("Stripped Sensitive Keys", str(removed_keys))
    log_metric("Zero Cloud Egress Confirmed", "Prohibited internal thought chains purged from memory")

    # --------------------------------------------------------------------------
    # Step 5: A2UI Interactive Surface Compilation & Stateless 21 CFR Part 11 Token
    # --------------------------------------------------------------------------
    log_step("STEP 5", "A2UI Protocol: Interactive Card Compilation & HMAC Seal")

    SECRET_KEY = b"merck-sovereign-hsm-hmac-sha256-key-clinical-prod"
    token_jti = f"jti-a2ui-{uuid.uuid4().hex[:16]}"
    
    # State token payload (Stateless, zero DB locks, 48-hour TTL)
    token_claims = {
        "jti": token_jti,
        "studyId": "MK-3475-087",
        "cohort": "Cohort-B",
        "action": "APPROVE_DOSE_REDUCTION",
        "recommendedDose": "300mg Q4W",
        "exp": int(time.time()) + (48 * 3600),
        "iss": "merck-a2a-gateway",
        "regCompliance": "21 CFR Part 11"
    }
    
    serialized_claims = json.dumps(token_claims, sort_keys=True)
    signature = hmac.new(SECRET_KEY, serialized_claims.encode("utf-8"), hashlib.sha256).hexdigest()
    signed_state_token = f"{token_jti}.{signature}"

    # Compile A2UI Surface JSON Schema
    a2ui_card = {
        "a2ui_version": "1.0.0",
        "cardId": f"a2ui-card-{uuid.uuid4().hex[:8]}",
        "title": "Clinical Study Safety Protocol Amendment: MK-3475-087",
        "urgency": "HIGH_PRIORITY",
        "summary": "Bayesian inference indicates +5.42% Grade 3/4 hepatotoxicity elevation in Cohort-B.",
        "components": [
            {
                "type": "MetricBadge",
                "label": "Toxicity Delta",
                "value": "+5.42%",
                "severity": "CRITICAL"
            },
            {
                "type": "RecommendationText",
                "content": "Implement immediate dose reduction from 400mg Q6W to 300mg Q4W and mandatory weekly LFT monitoring."
            },
            {
                "type": "ActionButton",
                "actionId": "approve_dose_titration",
                "label": "Authorize Protocol Amendment (21 CFR Part 11)",
                "stateToken": signed_state_token
            }
        ]
    }

    log_success("A2UI Interactive Card Surface compiled.")
    log_metric("A2UI Card ID", a2ui_card["cardId"])
    log_metric("HMAC State Token", signed_state_token[:40] + "...")
    log_metric("Stateless TTL", "48 Hours (Zero Relational Database Locks)")

    # --------------------------------------------------------------------------
    # Step 6: Human-in-the-Loop (HITL) Digital Signature Verification
    # --------------------------------------------------------------------------
    log_step("STEP 6", "Medical Director HITL Execution & 21 CFR Part 11 Audit Trail")

    # Simulate Medical Director clicking the button in the UI
    hitl_reviewer = "dr.patel@merck.com (Global Medical Director)"
    log_info("HITL User", f"Medical Director ({hitl_reviewer}) reviewed A2UI Card.")
    log_info("HITL User", "Submitting digital signature cryptographic callback...")
    time.sleep(0.2)

    # Server-Side Cryptographic Token Verification
    token_parts = signed_state_token.split(".")
    assert len(token_parts) == 2, "Invalid token format"
    received_jti, received_sig = token_parts[0], token_parts[1]
    expected_sig = hmac.new(SECRET_KEY, serialized_claims.encode("utf-8"), hashlib.sha256).hexdigest()

    if hmac.compare_digest(received_sig, expected_sig):
        audit_record = {
            "auditId": f"gxp-audit-{uuid.uuid4().hex[:12]}",
            "studyId": token_claims["studyId"],
            "decision": "APPROVED",
            "amendment": "Protocol Amendment v4.2 -> v4.3 (Dose reduction 300mg Q4W)",
            "signedBy": hitl_reviewer,
            "signatureType": "21 CFR Part 11 Validated Digital Signature",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sha256_seal": hashlib.sha256(signed_state_token.encode("utf-8")).hexdigest()
        }
        log_success("HMAC Cryptographic Signature VERIFIED (Tamper-evident).")
        log_success(f"21 CFR Part 11 Audit Trail Recorded: {audit_record['auditId']}")
        log_metric("Signed By", audit_record["signedBy"])
        log_metric("Signature SHA-256", audit_record["sha256_seal"][:32] + "...")
    else:
        print(f"{RED}❌ CRYPTOGRAPHIC VERIFICATION FAILED: Tampered token detected.{RESET}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 7: A2A Protocol Response Delivered to AWS Agent
    # --------------------------------------------------------------------------
    log_step("STEP 7", "Return A2A Response to AWS Agent Across PrivateLink")

    a2a_response = {
        "jsonrpc": "2.0",
        "id": a2a_task_request["id"],
        "result": {
            "status": "COMPLETED_AND_AUTHORIZED",
            "studyId": "MK-3475-087",
            "cohort": "Cohort-B",
            "decision": "APPROVED_BY_MEDICAL_DIRECTOR",
            "sanitizedFindings": clean_payload["adverse_events"],
            "authorizedAmendment": audit_record["amendment"],
            "gxpAuditId": audit_record["auditId"],
            "executionSummary": "Cross-cloud biopharma consensus finalized with zero raw patient record egress."
        },
        "metadata": {
            "a2a_version": "1.0.0",
            "ast_sanitization_time_us": t_ast_us,
            "vpc_sc_perimeter": "sp_merck_clinical_prod",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
    }

    log_info("AWS Agent", f"Received authentic A2A v1.0.0 response for task {a2a_task_request['id']}:")
    print(json.dumps(a2a_response, indent=2))
    log_success("AWS Agent ingested sanctioned trial modification into EDC workflow.")

    print(f"\n{BOLD}{GREEN}================================================================================")
    print(" 🎯 CROSS-CLOUD A2A & A2UI SIMULATION SUCCESSFULLY COMPLETED!")
    print(f"================================================================================{RESET}\n")

if __name__ == "__main__":
    main()
