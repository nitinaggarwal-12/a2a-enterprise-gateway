# Option 3: Outside-In Platform Demarcation (Direct Vertex AI Bypass)

## Architectural Overview

Option 3 implements a clean **Dual-Plane Enterprise Architecture** that guarantees Enterprise complete sovereignty over its agent graphs, internal data tools, and reasoning loops while still utilizing Gemini Enterprise (GE) as an interactive Human-in-the-Loop (HITL) UI surface.

```
+-----------------------------------------------------------------------------------+
|  PLANE 1: BACKEND SOVEREIGN EXECUTION PLANE (Enterprise Controlled Infrastructure)     |
|                                                                                   |
|  +---------------------------+        +----------------------------------------+  |
|  | Enterprise Agent Orchestrator  | <----> | Internal EDC Clinical DB & RWE Warehouse| |
|  +---------------------------+        +----------------------------------------+  |
|               |                                                                   |
|               v                                                                   |
|  +---------------------------+                                                    |
|  | Google Cloud Vertex AI SDK| (Direct API Execution, Gemini 1.5 Pro)            |
|  +---------------------------+ (ZERO ADK Metadata Envelopes / Zero Pollution)     |
+-----------------------------------------------------------------------------------+
                                       |
                                       v (Asynchronous Dossier Hand-off)
+-----------------------------------------------------------------------------------+
|  PLANE 2: INTERACTION & HITL UI PRESENTATION PLANE (Gemini Enterprise Surface)   |
|                                                                                   |
|  +---------------------------+        +----------------------------------------+  |
|  | Plane 2 UI Bridge Service | -----> | Gemini Enterprise Inbound Webhook /    |  |
|  | (FastAPI + HMAC Sealing)  |        | Medical Director Workspace Canvas      |  |
|  +---------------------------+        +----------------------------------------+  |
|               ^                                           |                       |
|               |                                           | (User Clicks Approve) |
|               +-------------------------------------------+                       |
|                       (21 CFR Part 11 Audit Trail & Sign-Off)                     |
+-----------------------------------------------------------------------------------+
```

## Key Architectural Advantages

1. **Zero Metadata Leakage by Design**: Because Plane 1 executes directly against the Vertex AI Foundation API using standard Google Cloud SDK service accounts, no GE ADK runtime containers or `adk_metadata` envelopes are ever injected into the pipeline.
2. **Stateless 48-Hour HITL Lifecycles**: Action tokens embedded in A2UI cards are cryptographically sealed with HMAC-SHA256, allowing asynchronous approvals across multi-day clinical review cycles without in-memory state locks.
3. **21 CFR Part 11 Audit Trail**: User sign-offs through Gemini Enterprise are mapped directly into immutable audit trails with cryptographic verification hashes.

## Running the Simulation

```bash
# Execute the full end-to-end simulation
./test_e2e.sh
```
