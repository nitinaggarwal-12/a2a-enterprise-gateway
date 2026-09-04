# Engineering Guide: Context Management, Skills Architecture & Evolution

This document details the architectural decisions, context layers, documentation suite, executable skills, and knowledge graph evaluations implemented for the **Enterprise A2A Gateway** (`a2a-enterprise-gateway`).

---

## 1. Executive Summary & Purpose

AI coding assistants (Gemini, Claude Code, Antigravity, Cursor) are stateless across discrete sessions by default. Without grounded project context, agents suffer from:
1. **Blind File Wandering**: Burning 40–60% of tool calls and tokens grepping directories and reading irrelevant files.
2. **Context Drift & Hallucination**: Inventing non-standard APIs, breaking compliance guardrails (e.g. FDA 21 CFR Part 11), or violating latency budgets.
3. **Flaky Testing**: Interacting with dynamic browser DOMs without settling delays or theme awareness.

To solve this systematically, we built a **layered context, documentation, and verification architecture**:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             AGENT COGNITION STACK                                │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Layer 1: Agent Rules & Guardrails                                              │
│   ├── GEMINI.md       (System instructions, latency budgets, compliance rules)   │
│   ├── AGENTS.md       (Universal multi-agent coordination contract)              │
│   └── CLAUDE.md       (Pointer for Anthropic Claude Code)                        │
│                                                                                  │
│   Layer 2: Architectural & Regulatory Documentation Suite                         │
│   ├── ARCHITECTURE.md (3 production archetypes, data plane demarcation)          │
│   ├── SECURITY.md     (Zero clinical cloud egress, 21 CFR Part 11 matrix)       │
│   ├── RUNBOOK.md      (Operational runbook, ports, CLI execution recipes)        │
│   ├── CONTRIBUTING.md (PR quality gates, benchmark thresholds)                   │
│   └── CHANGELOG.md    (v1.0.0 release notes)                                     │
│                                                                                  │
│   Layer 3: Executable Verification Skills (`skills/*/SKILL.md`)                 │
│   ├── ast-sanitizer-benchmark    (Deterministic sub-28 µs AST latency check)    │
│   ├── gxp-21cfr11-token-verifier (HMAC-SHA256 signature & tamper rejection suite)│
│   └── dual-theme-chrome-e2e      (Google signed Chrome 45+ screenshot capture)   │
│                                                                                  │
│   Layer 4: Codebase Graph & Navigation (Evaluated)                               │
│   └── Graft (@nanonets/graft)    (Tree-sitter AST parsing; evaluated & scoped)  │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1: The Context & Rules Files

### Why not just one generic prompt?
Different tools read different configuration files at session initialization. Having dedicated, complementary files prevents duplicate maintenance while ensuring every agent tool enforces the same standards.

| File | Primary Consumer | Purpose & Contents |
| :--- | :--- | :--- |
| [`GEMINI.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/GEMINI.md) | **Google Gemini CLI / Antigravity** | Injected on turn 0 into the agent prompt. Defines non-negotiable engineering rules: sub-28 µs AST latency, stateless HMAC-SHA256 signatures, dual-theme WCAG AAA contrast, and Google signed Chrome E2E testing protocols. |
| [`AGENTS.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/AGENTS.md) | **Multi-Agent Swarms / Open Standard** | Standardized protocol file recognized by autonomous coding swarms. Establishes the Google A2A v1.0.0 protocol boundary, data demarcation rules, and tool references. |
| [`CLAUDE.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/CLAUDE.md) | **Anthropic Claude Code** | Acts as an explicit pointer directing Claude Code to read `GEMINI.md` and `AGENTS.md`, ensuring all agents adhere to identical conventions without diverging. |

---

## 3. Layer 2: The Engineering Documentation Suite

We established a comprehensive suite of markdown specifications to document every architectural, regulatory, and operational aspect of the platform:

### 1. [`ARCHITECTURE.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/ARCHITECTURE.md)
* **Why**: Prevents the AI from hallucinating arbitrary proxy patterns by explicitly defining the **Three Production Archetypes**:
  - **Option 1**: Cloud Run HTTP/JSON Interceptor Proxy (A2UI card transformations).
  - **Option 2**: Native `a2a.v1` gRPC Protobuf binary streaming service (`protos/a2a.proto`).
  - **Option 3**: Outside-In Dual-Plane Sovereign Demarcation separating private biopharma VPCs from public external workspaces.
* **Key Code**: Includes the exact recursive in-memory AST dictionary stripping algorithm (`sanitize_payload_ast`).

### 2. [`SECURITY.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/SECURITY.md)
* **Why**: Grounded compliance requirements for biopharma clinical trial data.
* **Key Guardrails**:
  - **Zero Clinical Cloud Egress**: Prohibits transmitting patient CDISC SDTM domain data (Adverse Events, Lab Results, Demographics) across untrusted external networks.
  - **FDA 21 CFR Part 11 Electronic Signatures**: Eliminates database lock contention by sealing state, signer identity, and meaning into tamper-evident 48-hour HMAC-SHA256 tokens.

### 3. [`RUNBOOK.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/RUNBOOK.md)
* **Why**: Operational runbook detailing exact port mappings, healthcheck endpoints, and shell recipes:
  - Starting the FastAPI portal (`python -m uvicorn portal.app:app --port 8090`).
  - Running pytest suites (`pytest -v`).
  - Running automated visual E2E screenshot captures (`bash run_visual_e2e_suite.sh`).
  - Resolving port collisions (`lsof -i :8090`).

### 4. [`CONTRIBUTING.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/CONTRIBUTING.md)
* **Why**: Sets strict quality gates for developers and autonomous agents submitting pull requests (sub-28 µs micro-benchmark passes, dual-theme screenshot evidence, conventional commit formats).

### 5. [`CHANGELOG.md`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/CHANGELOG.md)
* **Why**: Tracks release milestones, including the v1.0.0 Enterprise Gateway launch, Three.js 3D WebGL cockpit integration, Veo 2 studio, and Dr. A2A live voice assistant.

---

## 4. Layer 3: Executable Project Skills (`skills/*/SKILL.md`)

Unlike passive documentation, **Skills** are executable playbooks paired with standalone scripts that agents run dynamically to verify critical properties:

```text
skills/
├── ast-sanitizer-benchmark/
│   ├── SKILL.md              # Instructions on micro-benchmark execution & budget
│   └── scripts/benchmark_ast.py  # 10,000 iteration AST sanitizer timing harness
├── gxp-21cfr11-token-verifier/
│   ├── SKILL.md              # Instructions on FDA Part 11 token verification
│   └── scripts/verify_tokens.py  # Cryptographic minting & tamper rejection suite
└── dual-theme-chrome-e2e/
    ├── SKILL.md              # Headless Chrome visual regression instructions
    └── scripts/verify_portal_e2e.js  # Dual-theme screenshot test runner
```

1. **`ast-sanitizer-benchmark`**: Executes 10,000 iterations measuring dictionary traversal latency. Proves empirical performance: **~5.95 µs mean latency** (well under the 28 µs regulatory budget) with zero regex backtracking.
2. **`gxp-21cfr11-token-verifier`**: Programmatically verifies token minting, tamper rejection (modifying payload, dose, or signature), and 48-hour TTL expiry to guarantee audit integrity.
3. **`dual-theme-chrome-e2e`**: Coordinates Google signed Chrome to capture high-resolution desktop screenshots with mandatory 800ms settling delays.

---

## 5. Layer 4: Codebase Knowledge Graph Evaluation (`Graft`)

We explored **Graft** ([`trailhq/Graft`](https://github.com/trailhq/Graft) / `@nanonets/graft`), an open-source codebase knowledge graph engine.

### How Graft Works:
* **Tree-sitter Parsing**: Parses 23+ languages into AST call graphs (`.graph/wiring.json`) with zero token cost.
* **3ms Working-Tree Invalidation**: Computes fast SHA tree fingerprints to reflect unstaged local edits instantly without re-embedding.
* **Agent Integration**: Exposes an MCP server (`graft mcp`) and CLI tools (`graft map`, `graft trace`, `graft grep`).

### Why We Skipped Graft for `a2a-enterprise-gateway`:
1. **Compact Codebase**: With ~10 core backend files, native `ripgrep` (`grep_search`) searches the entire repo in under 2ms.
2. **Single-File UI**: The frontend is concentrated in a single WebGL/Alpine HTML file (`portal/static/portal.html`). Tree-sitter cannot trace cross-language bindings between HTML attributes and inline JavaScript.
3. **Context Token Overhead**: Registering the Graft MCP server adds ~2,000 tokens of JSON schema definitions to every turn in the system prompt.

### Where Graft IS High Value:
* **Large, Modular Web Apps (like `zyvoriq`)**: In Next.js applications with 50+ React `.tsx` components, nested route handlers, and server actions, Graft maps component import trees, tracks function blast radius, and reduces agent token usage by ~42%.

---

## 6. E2E Test Suite Self-Correction & Workspace Hygiene

During our testing cycle, the test suite encountered and autonomously resolved a real-world integration issue:

### 1. The Challenge
The legacy E2E script attempted to query `#tab-onboarding` and `#btn-run-opt1`—outdated DOM IDs from an early prototype that had been replaced in the production portal.

### 2. The Self-Healing Fix
The test script was refactored from brittle DOM clicks to **direct Alpine.js reactive state manipulation**:
```javascript
const updateState = async (fn) => {
  await page.evaluate((fnStr) => {
    const state = Alpine.$data(document.querySelector('[x-data]'));
    const update = new Function('state', fnStr);
    update(state);
  }, fn.toString());
  await sleep(800); // Allow CSS transitions to settle
};
```
* Added programmatic theme switching: `setTheme(true)` (Dark) and `setTheme(false)` (Light).
* Added layout density testing (`compactMode = true`).
* Captured **45+ screenshots** across all 12 views in both Light and Dark modes.

### 3. Workspace Hygiene Enforcement
* Added `scratch/screenshots_*/` and `scratch/*.html` to [`.gitignore`](file:///Users/nitinagga/Documents/a2a-enterprise-gateway/.gitignore).
* Purged temporary `.chrome_profile_*` directories and added automated directory cleanup in the Puppeteer `finally` block.
* Cleaned up untracked files (`.mcp.json`, `.ignore`, `.claude/`), keeping the Git tree pristine.
* Committed and pushed all changes cleanly to `origin/main` ([commit `66fab82`](https://github.com/nitinagga/Documents/a2a-enterprise-gateway/)).

---

## 7. Summary Comparison Matrix

| Component | Category | When It Runs | Primary Benefit |
| :--- | :--- | :--- | :--- |
| **`GEMINI.md`** | Agent Rules | Prompt turn 0 | Injects non-negotiable architectural & compliance rules. |
| **`AGENTS.md`** | Protocol Spec | Prompt turn 0 | Universal multi-agent coordination contract across tools. |
| **`CLAUDE.md`** | Compatibility | Prompt turn 0 | Directs Claude Code to follow `GEMINI.md` / `AGENTS.md`. |
| **`ARCHITECTURE.md`** | Technical Spec | On demand / Reference | Explains 3 deployment archetypes & AST stripping. |
| **`SECURITY.md`** | Compliance Spec | On demand / Reference | Guarantees Zero Clinical Cloud Egress & 21 CFR Part 11. |
| **`RUNBOOK.md`** | Operations | On demand / Dev | Complete step-by-step developer and testing playbook. |
| **`skills/*`** | Verification | Test / CI/CD runs | Deterministic micro-benchmarks & tamper verification. |
| **`Graft`** | Knowledge Graph | Codebase navigation | AST call graphs & token reduction (optimal for large apps). |
