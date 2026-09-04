# Contributing to Enterprise A2A Gateway

Thank you for contributing to the **Enterprise A2A Gateway**. Because this project operates in a regulated biopharma environment subject to FDA 21 CFR Part 11 and GAMP 5 guidance, all contributions must adhere to the standards outlined below.

---

## 🌿 1. Branching & Commit Conventions

### Branch Naming
- Features: `feat/short-description`
- Bug Fixes: `fix/short-description`
- Documentation: `docs/short-description`
- Performance: `perf/short-description`

### Conventional Commit Messages
Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
```text
feat(portal): add Cmd+K omni command palette modal
fix(ast): prevent recursion depth error on cyclic payload
docs(gemini): update 21 CFR Part 11 audit guidelines
perf(sanitizer): optimize dictionary key stripping to 5.95 µs
```

---

## 🎨 2. UI/UX Design Standards

When modifying the single-page portal (`portal/static/portal.html`):

1. **Desktop-First Spacious Widths**:
   - Container elements must use `max-w-8xl` (1440px) or `max-w-[1600px]` with generous horizontal padding (`px-8 md:px-12`).
   - Sticky headers must span full width with edge-to-edge backdrop blur (`backdrop-blur-2xl`).

2. **Strict Dual-Theme WCAG AAA Contrast**:
   - Both **Dark** and **Light** modes must pass high-contrast readability checks.
   - Use CSS custom properties (`var(--color-bg-card)`, `var(--color-text-primary)`) rather than hardcoded hex values in component templates.

3. **Tactile Micro-Interactions**:
   - Prefer inline stateful cards (like the 1-Click HITL HMAC Certificate) over disruptive browser alert dialogs.

---

## 🧪 3. Quality Gate & Pre-Flight Verification

Before pushing code or opening a Pull Request:

1. **Run AST Benchmark**: Ensure key-stripping latency is under 28 µs:
   ```bash
   .venv/bin/python skills/ast-sanitizer-benchmark/scripts/benchmark_ast.py
   ```
2. **Run 21 CFR Part 11 Verifier**: Ensure token signing and tamper defense pass:
   ```bash
   .venv/bin/python skills/gxp-21cfr11-token-verifier/scripts/verify_tokens.py
   ```
3. **Execute E2E Headless Chrome Suite**: Ensure all 12 views pass without layout regression:
   ```bash
   NODE_PATH=node_modules node scratch/run_dual_theme_e2e.js
   ```

---

## 🔒 4. Regulatory & Security Rules

- **Zero Clinical Cloud Egress**: Never transmit raw CDISC SDTM data or internal system instructions across unencrypted public networks.
- **AST Integrity**: Never bypass `sanitize_payload_ast()` for outbound payloads.
- **Stateless Tokens**: Never introduce relational database write-locks into the HITL approval flow.
