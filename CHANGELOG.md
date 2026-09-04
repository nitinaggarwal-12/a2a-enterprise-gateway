# Changelog: Enterprise A2A Gateway

All notable changes to this project are documented in this file in accordance with [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/).

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
