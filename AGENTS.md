# Multi-Agent Coordination Guidelines (AGENTS.md)

Welcome to the **Enterprise A2A Gateway** agent workspace. This document provides standardized system instructions for all autonomous coding agents, subagents, and LLM copilots operating in this repository.

---

## 🎯 Primary Directives

1. **Protocol Adherence**: All inter-agent and external communications must adhere strictly to the **Google Agent-to-Agent (A2A) v1.0.0 Protocol** (`protos/a2a.proto`).
2. **Sub-28 µs AST Sanitization**: Outbound payloads leaving internal sovereign biopharma enclaves must be filtered through `sanitize_payload_ast()` to strip internal orchestrator envelopes (`__internal_trace__`, `adk_internal_context`, prompt injection flags). Never introduce regular expressions into the hot path.
3. **Stateless 21 CFR Part 11 Electronic Signatures**: Use 48-hour HMAC-SHA256 signed state tokens for human-in-the-loop (HITL) dose titration workflows. Never introduce relational database write-locks into approval flows.
4. **Strict Dual-Theme WCAG AAA Contrast**: All frontend modifications in `portal/static/portal.html` must render cleanly in both Dark Mode (`.dark`) and Light Mode (`.light`).
5. **Google Signed Chrome E2E Verification**: Every UI transition must be verified using `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` with mandatory 800ms settling delays (`await sleep(800)`).
6. **Autonomous Issue Remediation (Fix Without Asking)**: To fix an issue, **NEVER ask for approval**. Just fix it, evaluate it, and if the same or other issues are found, fix those and keep doing it continuously until the goal is achieved and verified.
7. **Deep State-Mutation Quality Gates**: Never rely on shallow router assertions (`activeTab === key`) or static mockup screenshots. Every workspace must be audited via automated headless Chrome tests with live user interactions (button click → backend API response → DOM mutation → cryptographic security rejection).

---

## 🛠️ Canonical Tooling & Commands

- **FastAPI Portal**: `.venv/bin/python -m uvicorn portal.app:app --host 127.0.0.1 --port 8090 --reload`
- **Master 4-Step E2E Quality Gate**: `./test_all_options.sh` (Pytest + Options 1-3 CLI + Headless Chrome E2E)
- **Restored Tabs Behavioral E2E**: `NODE_PATH=node_modules node scratch/test_all_restored_tabs.js`
- **Canonical Dual-Theme Suite**: `NODE_PATH=node_modules node scratch/run_dual_theme_e2e.js`
- **AST Micro-Benchmark**: `.venv/bin/python skills/ast-sanitizer-benchmark/scripts/benchmark_ast.py`
- **Token Cryptography Suite**: `.venv/bin/python skills/gxp-21cfr11-token-verifier/scripts/verify_tokens.py`
- **Adversarial Chaos E2E Suite**: `NODE_PATH=node_modules node scratch/test_adversarial_oddities_e2e.js`

---

## 📁 Repository Customizations
- **Project Rules**: See [`GEMINI.md`](./GEMINI.md) for global project constraints.
- **Skills Directory**: See [`skills/`](./skills/) for executable runbooks and scripts.
- **Lifecycle Quality Hooks**: See [`hooks.json`](./hooks.json) and [`_agents/hooks.json`](./_agents/hooks.json) for automatic pre/post tool compilation and quality verification.
