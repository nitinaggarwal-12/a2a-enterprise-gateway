# Enterprise A2A (Agent-to-Agent) Gateway — Project Rules & Guidelines

Welcome to the **Enterprise A2A Gateway**. This document outlines repository architecture, tech stack specifications, execution commands, coding conventions, and compliance rules for all AI agents and developers working in this codebase.

---

## 🏛️ Project Overview & Purpose

The Enterprise A2A Gateway provides a sovereign, high-throughput gateway implementing the **Google Agent-to-Agent (A2A) v1.0.0 Protocol** tailored for biopharma clinical trial swarms and multi-agent coordination.

### Core Architecture Highlights
1. **Microsecond AST ADK Sanitizer**: Strips prohibited orchestration envelopes (such as `__internal_trace__`, `adk_internal_context`) in memory in **under 28 µs** with zero regular-expression backtracking.
2. **Stateless 21 CFR Part 11 Signatures**: Generates and verifies tamper-evident HMAC-SHA256 signed state tokens with 48-hour TTL, eliminating database lock contention.
3. **Three Production Archetypes**:
   - **Option 1**: Cloud Run HTTP/JSON Interceptor Proxy for standard webhooks and A2UI card transformations.
   - **Option 2**: Native `a2a.v1` gRPC Protobuf binary streaming service with typed intermediate thought traces.
   - **Option 3**: Outside-In Dual-Plane Demarcation physically separating sovereign biopharma VPCs from external Gemini Enterprise workspaces.
4. **Multimodal Visual Verification Portal (`portal/static/portal.html`)**:
   - **Three.js 3D WebGL Engine**: Undulating terrain mesh, rotating double-helix Veo stage, and spinning 3D copilot avatar.
   - **Google DeepMind Veo 2 Studio**: 5-Act executive 4K storyboard generator with orbital 3D camera controls.
   - **Gemini Omni Live Voice & Teleprompter**: Bidirectional WebRTC audio streaming with live speech-to-text transcript ticker.
   - **Omni Command Palette (`⌘K` / `Ctrl+K`)**: Instant action registry indexing all 12 workspaces, 4 personas, and Technical FAQ.
   - **Information Density Switcher**: Dynamic viewport toggle between `Comfortable` and `Compact` spacing.
   - **Technical FAQ Knowledge Base**: In-depth architecture Q&As with code snippets and interactive bridges.

---

## 💻 Tech Stack Specifications

- **Backend**: Python 3.11+, FastAPI (`portal/app.py`), Uvicorn, Pydantic v2, `hashlib`/`hmac` standard libraries.
- **Protocol Schemas**: Google `a2a.v1.0.0` Protocol Buffer schemas (`protos/a2a.proto`).
- **Frontend**: Single-Page Portal (`portal/static/portal.html`), Alpine.js v3, Tailwind CSS, Three.js (WebGL 3D), FontAwesome 6.5, Canvas Confetti.
- **E2E Automation**: Node.js, Puppeteer running exclusively against **Google signed Chrome for macOS**.

---

## 🛠️ Build, Run, & Test Commands

### 1. Start FastAPI Local Portal Server
```bash
# Run server on port 8090 with hot-reload enabled
.venv/bin/python -m uvicorn portal.app:app --host 127.0.0.1 --port 8090 --reload
```
*Portal will be live at `http://127.0.0.1:8090`.*

### 2. Run Comprehensive Dual-Theme E2E Test Suite
```bash
# Executes automated headless Chrome verification across all 12 views in Light & Dark modes
NODE_PATH=node_modules node scratch/run_dual_theme_e2e.js
```
*Screenshots are automatically output to `docs/screenshots/` and `portal/static/screenshots/`.*

### 3. Python Unit & Security Tests
```bash
.venv/bin/pytest -v
```

---

## 🎨 UI/UX & Design System Rules

1. **Desktop-First Layouts**:
   - Primary content container must use wide widths (`max-w-8xl` / 1440px or `max-w-[1600px]`) with generous padding (`px-8 md:px-12`).
   - Sticky headers must span full width with edge-to-edge backdrop blur (`backdrop-blur-2xl`).

2. **Strict Dual-Theme WCAG AAA Contrast**:
   - Both **Dark** (`.dark`) and **Light** (`.light`) modes must maintain crisp contrast ratios.
   - Use CSS custom property variables (`var(--color-bg-card)`, `var(--color-text-primary)`, `var(--color-badge-emerald-text)`) instead of hardcoded hex values in component bodies.

3. **Tactile Micro-Interactions & Stable Layouts**:
   - Prefer inline stateful cards (like the 1-Click HITL HMAC Certificate) over disruptive browser alert dialogs.
   - **Zero Tilting Screens**: Strictly prohibit 3D tilt/rotation interactions (`perspective`, `rotateX`, `rotateY`) on screens, containers, and cards. Keep all surfaces stable, planar, and distortion-free.

---

## 🧪 E2E Testing & Verification Protocol

1. **Google Signed Chrome Only**:
   - All Puppeteer automation must specify the signed binary path:
     `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
2. **Mandatory 800ms Settling Delays**:
   - Always inject `await sleep(800)` immediately following tab transitions, drawer opens, or state toggles to permit Alpine.js and CSS transitions to settle before screenshot capture.
3. **DOM-Level Click Discipline**:
   - Prefer direct DOM clicks (`page.$eval(selector, el => el.click())`) over physical coordinate clicks to prevent click interception by modal scrims.
4. **Direct String Inspection**:
   - Always verify that target DOM nodes physically exist and render expected text content (e.g. `AST Latency`, `HMAC-SHA256`, `21 CFR Part 11`) rather than relying solely on HTTP 200 or CLI exit codes.

---

## 🔒 Security & Regulatory Guardrails

- **Zero Clinical Cloud Egress**: Sensitive clinical trial records (CDISC SDTM domains) and raw system prompts must never be transmitted across unencrypted boundaries or used for public foundational model training.
- **AST Sanitization Integrity**: Never bypass the in-memory AST dictionary filter (`sanitize_payload_ast`). All outbound payloads must strip prohibited keys.
- **Stateless Tokens**: Never introduce relational database write-locks into the HITL approval flow; preserve stateless HMAC-SHA256 token verification.
- **Git Hygiene**: Do not commit temporary Chrome profiles (`.chrome_profile_*`), raw logs, or `.env` credential files. Scratch scripts belong in `scratch/`.
