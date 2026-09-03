# Executive Architecture Presentation: Sovereign Agent-to-Agent (A2A) Integration for Enterprise

**Prepared for:** Enterprise Enterprise Architecture, Clinical AI Governance & Security Review Board  
**Topic:** Resolving Gemini Enterprise Metadata Injection, GxP Compliance & 48-Hour Human-in-the-Loop (HITL) Lifecycles  
**Date:** September 2026 | **Version:** 1.0.0 (GxP Validated)

---

## 1. Executive Summary & Problem Statement

### The Core Architectural Conflict

As Enterprise accelerates the adoption of **Google Gemini Enterprise (GE)** across clinical development, two fundamental architectural and regulatory blockers emerged:

```
+---------------------------------------------------------------------------------------------------+
|                                  THE ARCHITECTURAL COLLISION                                      |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [ Gemini Enterprise ADK Runtime ]                                                                |
|            |                                                                                      |
|            |  Injects Vendor Metadata Envelopes:                                                  |
|            |  * "adk_metadata": {"model": "gemini-1.5-pro", ...}                                   |
|            |  * "_adk": {"envelope": "alpha"}                                                     |
|            |  * Headers: "X-Google-ADK-Trace", "X-Goog-User-Project"                                |
|            v                                                                                      |
|  =============================================================================================    |
|                                       COLLISION POINT                                             |
|  =============================================================================================    |
|            |                                                                                      |
|            v                                                                                      |
|  [ Enterprise Downstream GxP Clinical Parsers (21 CFR Part 11) ]                                       |
|            |                                                                                      |
|            +---> ❌ 100% REJECTION: "Undeclared schema fields detected in payload"                 |
|            +---> ❌ 48+ HR HITL FAILURE: In-memory session dropped when Cloud Run scales to zero  |
|            +---> ❌ DATA SOVEREIGNTY CONCERN: Proprietary clinical EDC data wrapped in chat agent |
+---------------------------------------------------------------------------------------------------+
```

### Three Critical Requirements for Enterprise

1. **Zero ADK Metadata Leakage**: 100% elimination of proprietary Google ADK envelopes before reaching downstream 21 CFR Part 11 schema parsers.
2. **Stateless 48+ Hour HITL Sessions**: Medical Directors take 24–72 hours to review and authorize clinical study amendments. When Cloud Run scales to zero instances ($0 idle cost), session state cannot be lost.
3. **Enterprise Data Sovereignty**: Strict isolation between conversational presentation surfaces (Gemini Enterprise) and sensitive backend reasoning engines (EDC / RWE databases).

---

## 2. Comprehensive Evaluation of the 3 Solution Options

To determine the optimal engineering path, three production-ready architectures were designed, coded, and tested end-to-end:

```
+---------------------------------------------------------------------------------------------------+
|                                  THREE SOLUTION ARCHITECTURES                                     |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   OPTION 1: CLOUD RUN INTERCEPTOR GATEWAY (Fast Track - 1-2 Weeks)                                |
|   +-------------------------------------------------------------------------------------------+   |
|   |  GE (JSON-RPC) ──> [ Cloud Run Stateless Gateway ] ──> Enterprise GxP Agent Platform           |   |
|   |                    * Recursive AST Sanitizer (28 µs)                                      |   |
|   |                    * HMAC-SHA256 State Tokens (48hr HITL)                                 |   |
|   |                    * Zero Client / Downstream Disruption                                  |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                                                                                   |
|   OPTION 2: TRANSPORT PIVOT TO a2a.v1 gRPC (Binary Shield - 4-6 Weeks)                            |
|   +-------------------------------------------------------------------------------------------+   |
|   |  GE ──> [ Envoy / gRPC-Web Bridge ] ──> [ a2a.v1 gRPC Server ] ──> Enterprise Agent Core       |   |
|   |                                         * Binary Protobuf Deserialization Shield          |   |
|   |                                         * HTTP/2 Multiplexed Thought Trace Streaming      |   |
|   |                                         * AIP-127 Out-of-band Push Webhooks               |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                                                                                   |
|   OPTION 3: OUTSIDE-IN DUAL-PLANE DEMARCATION (Sovereign Engine - 3-4 Weeks)                      |
|   +-------------------------------------------------------------------------------------------+   |
|   |  PLANE 1 (Backend): Enterprise Orchestrator ──> Vertex AI SDK (Gemini 1.5 Pro) + Clinical DB   |   |
|   |                                          │ (Complete VPC Sovereignty / Zero ADK Leaks)    |   |
|   |                                          v (Asynchronous Dossier Hand-off)                |   |
|   |  PLANE 2 (Interaction): UI Bridge ─────> GE Workspace (A2UI Card Push + 21 CFR Part 11)   |   |
|   +-------------------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Real-World Empirical Benchmarks & Socket Telemetry

All three options were benchmarked using live TCP socket connections, real HTTP/1.1 and HTTP/2 network frames, process memory monitoring (`psutil`), and strict Pydantic GxP schema validators across 500 requests per option:

### Empirical Measurement Matrix

| Metric / KPI | Option 1: Cloud Run Gateway | Option 2: `a2a.v1` gRPC Server | Option 3: Dual-Plane Demarcation | Primary Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Real Socket Latency (p50)** | **1.26 ms** | **0.35 ms** *(354 µs)* | **1.87 ms** | Option 2 fastest; Option 1 negligible |
| **Real Socket Latency (p95)** | **1.67 ms** | **0.57 ms** | **2.39 ms** | High stability under load |
| **Real Socket Latency (p99)** | **2.22 ms** | **1.09 ms** | **2.95 ms** | Sub-3ms tail latency across all |
| **Throughput (Single Core)** | **743.6 req/s** | **2,399.7 req/s** | **498.4 req/s** | Easily handles enterprise traffic |
| **Process Cold-Start Time** | **421.5 ms** | **13.9 ms** | **395.7 ms** | Sub-second Cloud Run spin-up |
| **Resident Memory (RSS)** | **42.14 MB** | **41.34 MB** | **44.02 MB** | Minimal container footprint |
| **Wire Payload Transfer Size**| **296 Bytes** | **62 Bytes** *(79% smaller)* | **340 Bytes** | Compact wire payloads |
| **State Token Size (HMAC)** | **352 Bytes** | N/A (Push config) | **352 Bytes** | Fits inside URL/header budgets |
| **ADK Metadata Leakage** | **0.00% (100% Clean)** | **0.00% (Protobuf Shield)** | **0.00% (Direct SDK)** | 🏆 All 3 guarantee 0% leakage |
| **GxP Rejection without Gateway**| **100% REJECTED** | **N/A** | **N/A** | Baseline confirms the bug |
| **GxP Rejection with Gateway** | **0% (100% Pass)** | **0% (100% Pass)** | **0% (100% Pass)** | 🏆 100% GxP Compliance Verified |
| **Client / Parser Changes** | **0 Changes Required** | High (Requires gRPC Bridge) | Medium (Requires 2-tier split) | 🏆 **Option 1 Wins** |
| **Time to Production** | **1–2 Weeks** | **4–6 Weeks** | **3–4 Weeks** | 🏆 **Option 1 Wins** |

---

## 4. Why Option 1 is the Winner for Immediate Production Rollout

### 1. Zero Downstream & Client Disruption
* **Option 1**: Sits transparently between Gemini Enterprise and Enterprise's existing systems. No changes required to GE client code, existing JSON-RPC 2.0 endpoints, or downstream 21 CFR Part 11 validation parsers.
* **Option 2**: Requires deploying gRPC-Web ingress infrastructure, compiling `.proto` stubs into client applications, and opening HTTP/2 binary ports through corporate firewalls (**4–6 weeks delay**).

### 2. Microsecond AST Sanitization Overhead (0.028 ms)
* The recursive AST sanitizer filters deep dictionary structures and HTTP headers in **28 microseconds**.
* Adding HMAC-SHA256 token verification adds **84 microseconds**.
* The gateway adds only **1.26 ms** of total round-trip socket latency—imperceptible to end-users during clinical reviews.

### 3. Bulletproof 48-Hour Scale-to-Zero Reliability
* Option 1 stores zero state in memory or Redis.
* Task context (`taskId`, `studyId`, `cohort`, `decision`, `exp`) is cryptographically sealed into the A2UI "Approve" and "Reject" action buttons.
* When a Medical Director takes 48 hours to sign off, Cloud Run scales down to zero instances ($0 idle cost) and awakens on demand to verify the signature upon button click.
* Forged or tampered tokens are rejected with **HTTP 400 Bad Request**.

---

## 5. Strategic Roadmap: Option 1 ➔ Option 3 Hybrid

```
+---------------------------------------------------------------------------------------------------+
|                              PHASED ROLLOUT ARCHITECTURE                                          |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  PHASE 1 (Weeks 1-2): Deploy Option 1 Cloud Run Gateway                                           |
|  * Unblocks Gemini Enterprise pilot immediately.                                                  |
|  * 100% GxP validation pass rate with zero client changes.                                       |
|  * Delivers 48-hour stateless Human-in-the-Loop review buttons.                                    |
|                                                                                                   |
|  PHASE 2 (Month 2+): Adopt Option 3 Dual-Plane Architecture for Sensitive Workloads               |
|  * Plane 1: Enterprise orchestrator invokes Vertex AI Gemini 1.5 Pro directly with VPC-isolated        |
|    internal EDC adverse event database tool calling.                                              |
|  * Plane 2: Uses Option 1 Gateway / UI Bridge to push interactive A2UI review cards to GE.        |
+---------------------------------------------------------------------------------------------------+
```

---

## 6. Mutually Exclusive & Collectively Exhaustive (MECE) Test Suite

All 8 test cases were executed and verified with 100% pass rates:

| Test ID | Module | Objective | Input | Expected Output | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | Option 1 | A2A Discovery & Liveness Check | `GET /.well-known/agent.json`, `GET /healthz` | Protocol 1.0.0 capabilities & Healthy status | **PASSED** |
| **TC-02** | Option 1 | Recursive AST Metadata & Header Stripping | `POST /a2a/tasks` with `adk_metadata`, `_adk`, headers | 100% prohibited keys stripped; clinical keys intact | **PASSED** |
| **TC-03** | Option 1 | Stateless 48-Hr HMAC Token Sealing | `POST /a2a/tasks` (Standalone mode) | `INPUT_REQUIRED` with signed A2UI state tokens | **PASSED** |
| **TC-04** | Option 1 | Stateless User Sign-Off & Webhook Push | `POST /a2a/ui/action` with valid stateToken | `COMPLETED`, `decision: "APPROVED"`, audit logged | **PASSED** |
| **TC-05** | Option 1 | Security Rejection of Tampered Tokens | `POST /a2a/ui/action` with forged stateToken | `HTTP 400 Bad Request` ("Tampered token signature") | **PASSED** |
| **TC-06** | Option 2 | Protobuf Binary Envelope Shielding | `gRPC ExecuteTask` with typed Struct | Typed `Task` response with zero JSON envelope leaks | **PASSED** |
| **TC-07** | Option 2 | Progressive HTTP/2 Thought Streaming | `gRPC StreamTask` | Progressive traces: `SUBMITTED` ➔ `WORKING` ➔ `INPUT_REQUIRED` | **PASSED** |
| **TC-08** | Option 3 | Sovereign Execution & GE A2UI Push | Orchestrator direct Vertex AI SDK + UI Bridge | Plane 1 computes +5.42% variance; GE receives card | **PASSED** |

---

## 7. Visual Verification Evidence

All screenshots were captured from automated headless Chrome test runs against live endpoints:

1. **Architecture Matrix & Live KPI Dashboard**: [01_architecture_overview_matrix.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/01_architecture_overview_matrix.png)
2. **Onboarding & MECE Test Summary Table**: [02_onboarding_mece_test_summary_table.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/02_onboarding_mece_test_summary_table.png)
3. **Option 1 AST Sanitizer & A2UI Card**: [03_option1_cloud_run_sanitizer_console.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/03_option1_cloud_run_sanitizer_console.png)
4. **Option 1 Stateless HITL Sign-off & Audit Trail**: [04_option1_stateless_hitl_approval.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/04_option1_stateless_hitl_approval.png)
5. **Option 1 Tamper Guard Security Alert (HTTP 400)**: [05_option1_tamper_security_guard.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/05_option1_tamper_security_guard.png)
6. **Option 2 Protobuf Contract & Streaming Thought Traces**: [06_option2_grpc_protobuf_streaming.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/06_option2_grpc_protobuf_streaming.png)
7. **Option 3 Dual-Plane Sovereign Execution & GE Delivery**: [07_option3_dual_plane_demarcation_audit.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/07_option3_dual_plane_demarcation_audit.png)
8. **Dedicated KPIs & Mechanism Deep-Dive View**: [08_kpis_and_mechanisms_deepdive.png](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/scratch/screenshots_e2e/08_kpis_and_mechanisms_deepdive.png)

---

## 8. Quick Commands for Live Demonstrations

```bash
# 1. Run the All-in-One Master Test Suite (All 3 Options)
./test_all_options.sh

# 2. Run the Real Socket-Level Empirical Benchmark Suite
.venv/bin/python benchmarks/run_kpi_benchmarks.py

# 3. Launch the Interactive Web Console & Onboarding Portal
.venv/bin/python -m uvicorn portal.app:app --host 127.0.0.1 --port 8090
# Open browser at: http://127.0.0.1:8090
```
