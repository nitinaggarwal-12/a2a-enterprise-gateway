# Changelog: Enterprise A2A Gateway

All notable changes to this project are documented in this file in accordance with [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-09-10

### 🚀 Restored & Fully Interactive
- **Option 1: Cloud Run Interceptor Gateway (`opt1`)**:
  - Full interactive 3-stage pipeline UI with real-time AST Key Pruning (28 µs), Text Block Unwrapper (Case 74980079), and HMAC State Sealer (48h TTL).
  - Contaminated JSON payload editor with preset toggles (`Case 74980079 Contaminated` vs `Standard CDISC`).
  - Live Inbound Dispatch Probe calling `POST /api/option1/test-dispatch` with side-by-side AST stripped key diff and sealed state token inspector.
  - Stateless 21 CFR Part 11 Electronic Signature verification (`POST /api/option1/test-action`) with sub-millisecond approval and live cyber-tamper simulation validating HTTP 400 rejection.
- **Option 2: a2a.v1 gRPC Protobuf Contract (`opt2`)**:
  - Live HTTP/2 server-streaming reasoning trace terminal (`GET /api/option2/stream-simulation`) with animated progress bar and progressive status transitions (`SUBMITTED` → `WORKING` → `INPUT_REQUIRED`).
  - Interactive multi-tab schema explorer for `Service RPCs`, `Task Schema`, and `A2UI Action` contracts.
- **Option 3: Outside-In Dual-Plane Demarcation (`opt3`)**:
  - Live dual-plane pipeline execution console (`POST /api/option3/execute-pipeline`) demonstrating Sovereign Biopharma VPC Plane 1 (direct in-VPC Vertex AI reasoning over raw CDISC records) vs Gemini Enterprise Plane 2 (A2UI presentation surface).
  - Zero Clinical Cloud Egress verification badge and Demarcation Security Standards panel (PSC, VPC-SC, Ed25519 PKI).
- **Tool Integrations Hub (`integrations`)**:
  - Replaced static HTML mockups with dynamic Alpine.js reactive catalog (`GET /api/integrations/catalog`) supporting 8 enterprise connectors.
  - Interactive category filter chips (`All Platforms`, `Data Lakehouse`, `Clinical EDC`, `Collaboration`, `Identity & Access`, `Enterprise Ops`).
  - Live connection status toggling (`POST /api/integrations/toggle`) and inspection modal with live mTLS handshake probe (`POST /api/integrations/test-ping`).
- **Real-Time KPI Telemetry & Cost Modeling (`kpis`)**:
  - Live socket benchmark runner (`POST /api/kpi-benchmarks/run`) dynamically updating 5 speedometer cards.
  - Interactive Serverless Scale-to-Zero vs Always-On Kubernetes cost simulator with dynamic volume slider (100k to 50M requests/month).
- **Architecture Overview & MECE Matrix (`overview`)**:
  - 8-dimensional comparative matrix across Option 1, Option 2, and Option 3.
  - Interactive persona selector (`Architect`, `Clinician`, `Compliance`, `Developer`) displaying personalized adoption recommendations.
- **Workflow Playground & Content Ingestion (`playground`)**:
  - 1-click clinical dataset presets (`CDISC SDTM AE.csv`, `FHIR EHR Observation`, `Case 74980079 Contaminated`).
  - Live swarm execution pipeline with 4-stage validation checkmarks and real-time sanitized JSON output.

### 🛡️ Quality Gate & E2E Testing Hardening
- **Master Test Suite Integration (`test_all_options.sh`)**: Added Step [4/4] executing mandatory headless Google Signed Chrome E2E browser quality gate.
- **Canonical Dual-Theme Test Suite (`scratch/run_dual_theme_e2e.js`)**: Updated to verify all 16 views across Light and Dark modes.
- **Active Behavioral Quality Gate (`scratch/test_all_restored_tabs.js`)**: Replaced shallow router assertions with deep DOM state-mutation assertions and tamper rejection checks.
- **Lifecycle Quality Hooks (`hooks.json` & `_agents/hooks.json`)**: Configured automatic post-tool compilation and quality gate enforcement.

---

## [1.0.0] - 2026-09-03

### 🚀 Added
- **Microsecond AST ADK Key Sanitizer**: In-memory recursive dictionary traversal stripping prohibited orchestration envelopes (`__internal_trace__`, `adk_internal_context`) in **under 28 µs** with zero regex backtracking.
- **Stateless FDA 21 CFR Part 11 Signatures**: Cryptographic HMAC-SHA256 state tokens with 48-hour statutory TTL, eliminating relational database write-lock contention in clinical dose titration approvals.
- **Three Production Archetypes**:
  - *Option 1*: Cloud Run HTTP/JSON Interceptor Proxy for standard webhooks and A2UI card transformations.
  - *Option 2*: Native `a2a.v1` gRPC Protobuf binary streaming service with typed intermediate thought traces.
  - *Option 3*: Outside-In Dual-Plane Demarcation isolating sovereign biopharma VPCs from Gemini Enterprise.
- **Multimodal Visual Verification Portal (`portal/static/portal.html`)**:
  - **Three.js 3D WebGL Engine**: Dynamic sine-wave terrain mesh, rotating 3D double-helix Veo stage, and icosahedron copilot avatar.
  - **Google DeepMind Veo 2 Studio**: 5-Act executive 4K video storyboard generator with orbital 3D camera controls.
  - **Dr. A2A Omni Live Voice & Teleprompter**: Bidirectional WebRTC audio streaming with live speech-to-text transcript ticker.
  - **Omni Command Palette (`⌘K` / `Ctrl+K`)**: Global keyboard search indexing all 12 studios, 4 personas, and Technical FAQ.
  - **Information Density Switcher**: Viewport toggle between `Comfortable` and `Compact` spacing.
  - **Collapsible Navigation Sidebar & Clean Header**: 3-category grouped navigation with mini GxP status indicator.
  - **Technical FAQ Knowledge Base**: In-depth architecture Q&As with code snippets and interactive bridges.
- **Automated Project Skills**:
  - `skills/ast-sanitizer-benchmark`: 10,000-iteration microsecond benchmark runner.
  - `skills/gxp-21cfr11-token-verifier`: 21 CFR Part 11 cryptographic signature and cyber-tamper validation suite.
  - `skills/dual-theme-chrome-e2e`: Automated Puppeteer E2E suite running exclusively against Google signed Chrome for macOS.
- **System Documentation**:
  - `GEMINI.md`: Project rules, guidelines, and execution standards.
  - `AGENTS.md`: Universal agent directives and protocols.
  - `ARCHITECTURE.md`: High-level system topology and sequence specifications.
  - `SECURITY.md`: Zero Clinical Cloud Egress policy and regulatory guardrails.
  - `RUNBOOK.md`: Operations and local troubleshooting guide.
  - `CONTRIBUTING.md`: Contribution and code review standards.
