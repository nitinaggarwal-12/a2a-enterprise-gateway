# Universal Agentic Coding Framework
## The 4-Layer Cognition, Context & Verification Architecture for Any Codebase

---

## 1. Executive Summary: Why Agentic Coding Fails Without a Framework

When AI coding agents (Gemini, Claude Code, Cursor, Codex, Antigravity) are introduced to an ungrounded codebase, they invariably encounter three systemic failure modes:

1. **The Amnesia & Drift Problem**: The model starts with zero memory on Turn 0. Without grounded rules, it hallucinates non-existent libraries, writes antipatterns, or violates latency and security constraints.
2. **The "Blind File Wandering" Problem**: The agent spends 40–60% of its turn budget and tokens running exploratory greps, listing directories, and reading whole files just to locate symbols.
3. **The Flaky Execution Problem**: Browser automation and E2E testing fail because the agent uses brittle coordinate clicks, ignores CSS/React transition settling delays, or tests only a single visual theme.

To eliminate these failure modes permanently, this framework standardizes a **4-Layer Cognition, Context & Verification Stack** adaptable to **any codebase**—whether a Next.js frontend (`zyvoriq`), a high-throughput Python microservice (`a2a-enterprise-gateway`), a Go distributed system, or a Rust backend.

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      UNIVERSAL AGENT COGNITION STACK                             │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Layer 1: Agent Rules & Guardrails (Loaded Turn 0)                              │
│   ├── GEMINI.md / CLAUDE.md / AGENTS.md / .cursorrules                           │
│   └── Inviolable constraints, tech stack boundaries, and execution recipes       │
│                                                                                  │
│   Layer 2: Standard Engineering Documentation Suite (On-Demand Reference)        │
│   ├── ARCHITECTURE.md (Topologies, data flows, algorithms)                       │
│   ├── SECURITY.md     (Threat model, authentication, boundary demarcations)      │
│   ├── RUNBOOK.md      (Exact dev commands, ports, troubleshooting, CI/CD)        │
│   ├── CONTRIBUTING.md (PR quality gates, benchmark thresholds)                   │
│   └── CHANGELOG.md    (SemVer releases & milestones)                             │
│                                                                                  │
│   Layer 3: Executable Project Skills (`skills/*/SKILL.md`) (Deterministic Code)  │
│   ├── Benchmark Skills  (Micro-benchmarks, latency & throughput budgets)         │
│   ├── Security Skills   (Crypto, token verification, boundary rejection suites)  │
│   └── E2E Visual Skills (Headless Chrome, multi-theme, settling delays)          │
│                                                                                  │
│   Layer 4: Codebase Graph & Navigation (Blast-Radius Intelligence)               │
│   └── Small repos (< 15 files): Native ripgrep (0 overhead)                      │
│   └── Large repos (50+ files):  Tree-sitter AST Knowledge Graph (Graft)          │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1: The Universal Rules Matrix

### Purpose
Injected into the agent's context window on **Turn 0**. It teaches the model *how to think, what not to touch, and how to execute tools in this specific codebase*.

### The Rule Files Ecosystem
Different AI coding assistants look for different configuration files. Rather than duplicating content, maintain **one primary canonical rules file** and point the others to it:

| File | Target Tool | Role |
| :--- | :--- | :--- |
| **`GEMINI.md`** | Google Gemini CLI, Antigravity | Canonical rules for Gemini-powered workflows. |
| **`CLAUDE.md`** | Anthropic Claude Code | Canonical rules or pointer for Claude Code. |
| **`AGENTS.md`** | Multi-Agent Swarms, OpenAI Codex, Open-source copilots | Open-standard universal coordination spec. |
| **`.cursorrules`** | Cursor IDE | IDE prompt overrides for in-editor completions. |

### Universal Boilerplate Template (`GEMINI.md` / `AGENTS.md`)
Copy and adapt this template for any repository:

```markdown
# [Project Name] — Agent System Rules & Guidelines

Welcome to [Project Name]. This document outlines repository architecture, tech stack specifications, execution commands, coding conventions, and compliance rules for all AI agents and developers.

---

## 1. Primary Directives & Inviolable Guardrails
1. **Performance Budget**: [e.g., Critical path algorithms must execute in < X ms. No regex backtracking on hot paths.]
2. **Security Boundary**: [e.g., Zero unencrypted external egress. All auth tokens must be signed with HMAC-SHA256.]
3. **Design System & Contrast**: [e.g., Strict WCAG AAA dual-theme compliance (Light & Dark mode). No hardcoded hex values in component bodies.]
4. **Testing Discipline**: [e.g., Mandatory 800ms settling delays before capturing UI screenshots. Google signed Chrome only.]

---

## 2. Tech Stack & Environment
- **Runtime**: [e.g., Node.js 20+ / Python 3.11+ / Go 1.22+]
- **Framework**: [e.g., Next.js 15 App Router / FastAPI / Gin]
- **Styling/UI**: [e.g., Tailwind CSS v3/v4 / Alpine.js / shadcn/ui]
- **Testing**: [e.g., Vitest / Pytest / Puppeteer / Playwright]

---

## 3. Canonical Execution Commands
```bash
# 1. Start Local Development Server
[e.g., npm run dev -- --port 3000  OR  uvicorn app.main:app --port 8080 --reload]

# 2. Run Test Suite
[e.g., npm test  OR  pytest -v]

# 3. Run Automated Visual E2E Suite
[e.g., node scripts/run_e2e.js]
```

---

## 4. Git & Workspace Hygiene
- Never commit credentials, `.env` files, or temporary browser cache profiles (`.chrome_profile_*`).
- All scratch scripts belong in `scratch/`, which must be excluded in `.gitignore`.
```

---

## 3. Layer 2: The Core Engineering Documentation Suite

Instead of dumping 10,000 lines of architectural prose into the prompt, split documentation into modular, single-responsibility files that the agent reads **on demand**:

```text
your-repo/
├── ARCHITECTURE.md    # System topology, data flow, component hierarchy
├── SECURITY.md        # Threat boundaries, auth matrix, compliance rules
├── RUNBOOK.md         # Operational handbook: dev, test, debug, ports
├── CONTRIBUTING.md    # Code quality gates, linting, PR conventions
├── CHANGELOG.md       # SemVer release history & milestone tracking
└── README.md          # Project elevator pitch & 3-minute quickstart
```

### Why This Specific Split?
1. **Context Window Efficiency**: When an agent is asked to fix a security vulnerability, it only reads [`SECURITY.md`](../SECURITY.md) (150 tokens) instead of a monolithic 15,000-token design doc.
2. **Zero Hallucination**: When writing new API endpoints, the agent reads [`ARCHITECTURE.md`](../ARCHITECTURE.md) to adhere to the existing architectural patterns rather than inventing custom abstractions.
3. **Consistent Onboarding**: A human engineer and an AI copilot use the exact same runbooks and contributing guidelines.

---

## 4. Layer 3: Executable Project Skills (`skills/*/SKILL.md`)

### The Concept: Documentation vs. Skills
* **Documentation** tells the agent *what* the rules are.
* **Skills** give the agent *code to execute* to verify that the rules were actually met.

A skill is a self-contained directory with a `SKILL.md` runbook and standalone scripts:

```text
skills/
└── [skill-name]/
    ├── SKILL.md             # YAML metadata, trigger conditions, and instructions
    └── scripts/
        └── verify_*.py/.js  # Deterministic test script with exit code 0 or 1
```

### The 3 Essential Skill Archetypes for Any Codebase

#### Archetype A: The Performance / Micro-Benchmark Skill
* **When to use**: Whenever your app has strict latency budgets (e.g. sub-30 µs parsers, sub-10ms DB queries, 60fps canvas animations).
* **Script**: Runs 1,000 to 10,000 iterations in a tight loop and fails if mean/p99 latency exceeds the threshold.

#### Archetype B: The Security & Boundary Integrity Skill
* **When to use**: Whenever your app handles auth tokens, cryptographic signatures, data egress boundaries, or sensitive patient/financial records.
* **Script**: Programmatically mints valid tokens, tampers with payloads, and verifies that the verification engine returns `False` / `401 Unauthorized`.

#### Archetype C: The Multimodal E2E Visual Verification Skill
* **When to use**: Any frontend web application (React, Next.js, Vue, Alpine).
* **Script**: Launches headless Chrome via Puppeteer/Playwright, sets specific viewport resolutions (e.g., 1600x1000 desktop), toggles light/dark themes, waits for settling, and captures screenshots to `docs/screenshots/`.

---

## 5. Layer 4: Codebase Knowledge Graphs (When & How to Index)

When should you use an AST knowledge graph like **Graft** ([`trailhq/Graft`](https://github.com/trailhq/Graft)), and when should you stick to native search tools?

### The Decision Matrix

```text
                           ┌────────────────────────┐
                           │ How complex is the     │
                           │ codebase architecture? │
                           └───────────┬────────────┘
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
      Small / Focused Codebase                    Large / Modular Codebase
      • < 15-20 core files                        • 50+ to 1,000+ files
      • Monolithic or flat structure              • Deeply nested directories
      • Single-file embedded UI                   • Modular components (Next.js/React)
      • Fast ripgrep (< 5ms)                      • Multi-file import/export webs
                 │                                           │
                 ▼                                           ▼
      [ NATIVE TOOLS ONLY ]                       [ DEPLOY GRAFT / AST GRAPH ]
      • ripgrep (grep_search)                     • npx @nanonets/graft init
      • fd (find_by_name)                         • graft map (Structural topology)
      • Zero background daemons                   • graft trace (Blast-radius tracing)
      • Zero MCP prompt token overhead            • graft grep (Symbol lookup)
                                                  • ~42% token reduction on refactors
```

### Why Deterministic AST (Tree-sitter) Beats Vector Embeddings (RAG) for Code
1. **Exact Precision**: Tree-sitter parses the exact syntax tree (classes, functions, calls). It doesn't guess based on cosine similarity or "vibe."
2. **Zero Ingestion Cost**: Tree-sitter runs locally on the CPU in milliseconds with zero LLM API costs.
3. **Real-time Freshness**: Graft's 3ms tree fingerprint check instantly invalidates only modified sub-trees without waiting for background batch vector re-indexing.

---

## 6. The Universal Self-Healing Test Harness Protocol

To make your test automation bulletproof against agent flakiness, enforce these three universal rules:

### Rule 1: Mandatory 800ms Settling Delays
Never capture a screenshot or inspect a DOM element immediately after clicking a tab or drawer. Always inject a minimum **800ms synchronization delay** (`await sleep(800)`) to allow CSS animations, Alpine/React state renders, and layout reflows to settle.

### Rule 2: Prefer Direct Framework State over Mouse Clicks
In modern reactive SPAs (React, Alpine, Vue), physical coordinate clicks can be intercepted by modal backdrops or layout shifts. Directly driving the framework's reactive state is vastly more deterministic:
```javascript
// Alpine.js Example:
await page.evaluate((tabName) => {
  const state = Alpine.$data(document.querySelector('[x-data]'));
  state.currentTab = tabName;
}, 'settings');
await sleep(800);
```

### Rule 3: Automated Browser Profile Lifecycle Cleanup
Always wrap browser sessions in `try / finally` blocks that delete temporary profile directories upon exit:
```javascript
try {
  // run tests...
} finally {
  await browser.close();
  try {
    if (fs.existsSync(tempProfileDir)) {
      fs.rmSync(tempProfileDir, { recursive: true, force: true });
    }
  } catch (e) {}
}
```

---

## 7. The 5-Step Bootstrapping Checklist for Any Repository

Follow this sequence to ground any repository in under 15 minutes:

- [ ] **Step 1: Workspace Git Hygiene**
  Ensure `.gitignore` excludes `scratch/`, `*.log`, `.chrome_profile_*`, and local cache folders.
- [ ] **Step 2: Bootstrap Layer 1 (Rules)**
  Create `GEMINI.md` and `AGENTS.md` using the Universal Boilerplate Template in Section 2. Add `CLAUDE.md` pointing to them.
- [ ] **Step 3: Generate Layer 2 (Documentation Suite)**
  Create `ARCHITECTURE.md`, `SECURITY.md`, and `RUNBOOK.md` documenting your exact tech stack, ports, and dev commands.
- [ ] **Step 4: Scaffold Layer 3 (Executable Skills)**
  Add at least one verification skill (e.g. `skills/dual-theme-chrome-e2e/` or a micro-benchmark suite) so the agent can independently verify its own code.
- [ ] **Step 5: Evaluate Layer 4 (Graph Indexing)**
  - If repo has > 50 modular files (like `zyvoriq`): Run `npx @nanonets/graft init` to build local AST call graph cards.
  - If repo is compact (like `a2a-enterprise-gateway`): Rely on native `ripgrep` to keep context prompts lean.
