---
name: dual-theme-chrome-e2e
description: >-
  Use this skill whenever running automated end-to-end (E2E) verification for the
  Enterprise A2A Gateway visual portal across Dark Mode and Light Mode. Enforces
  Google signed Chrome on macOS, 800ms settling delays, and screenshot generation.
---

# Dual-Theme Google Signed Chrome E2E Automation

This skill automates visual and functional end-to-end verification for the Enterprise A2A Gateway single-page application (`portal/static/portal.html`).

## Strict Execution Protocols
1. **Google Signed Chrome Only**: All test instances must execute against `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
2. **Mandatory 800ms Settling Delays**: All view transitions, drawer opens, and theme toggles must wait `await sleep(800)` before screenshot capture to allow CSS and WebGL render loops to settle.
3. **DOM-Level Clicks**: Prefer direct DOM clicks (`page.$eval(selector, el => el.click())`) to prevent interception by modal scrims.

## Execution Steps

### Step 1: Ensure Local Server is Running
```bash
.venv/bin/python -m uvicorn portal.app:app --host 127.0.0.1 --port 8090 --reload
```

### Step 2: Execute E2E Suite
Run the test runner using Node.js:

```bash
NODE_PATH=node_modules node scratch/run_dual_theme_e2e.js
```

### Step 3: Verification Output
Artifacts are automatically saved to:
- `docs/screenshots/` (for repository documentation)
- `portal/static/screenshots/` (for live portal static asset serving)
- `scratch/screenshots_e2e/` (for local verification inspection)
