# Operations & Maintenance Runbook: Enterprise A2A Gateway

This runbook provides step-by-step procedures for local development, automated testing, benchmarking, and operational troubleshooting for the Enterprise A2A Gateway.

---

## 🚀 1. Local Development Setup

### Prerequisites
- **Python**: Version 3.11 or higher
- **Node.js**: Version 18 or higher
- **Browser**: Google Chrome for macOS (`/Applications/Google Chrome.app`)

### Virtual Environment Initialization
```bash
# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
npm install
```

---

## 🖥️ 2. Starting the Visual Portal Daemon

The visual portal runs on **port 8090** powered by Uvicorn and FastAPI:

```bash
# Start server with hot-reload enabled
.venv/bin/python -m uvicorn portal.app:app --host 127.0.0.1 --port 8090 --reload
```

- **Live URL**: `http://127.0.0.1:8090`
- **Health Check**: `http://127.0.0.1:8090/healthz` (returns HTTP 200 `{"status": "ok"}`)

---

## 🧪 3. Running Automated E2E Verification Suites

### 3.1 Master 4-Step E2E Quality Gate
Executes Pytest unit tests, Options 1-3 backend CLI tests, and the headless Google Chrome E2E browser quality gate:
```bash
./test_all_options.sh
```

### 3.2 Restored Tabs Behavioral Verification Suite
Executes live state-mutation, AST key stripping diff inspection, and cyber-tamper rejection tests across all restored workspaces:
```bash
NODE_PATH=node_modules node scratch/test_all_restored_tabs.js
```

### 3.3 Canonical Dual-Theme Screenshot Suite
The E2E test harness verifies all 16 views in both Dark and Light modes using Google signed Chrome:
```bash
# Execute headless dual-theme suite
NODE_PATH=node_modules node scratch/run_dual_theme_e2e.js
```

### 3.4 Adversarial, Odd-One-Out & SRE Chaos Suite
Executes 7 edge-case chaos simulations including Zalgo/Unicode AST stress testing, JTI nonce replay attacks, statutory token expirations, SSRF metadata probing, and live Chrome 503 circuit-breaker trip & DLQ re-drive:
```bash
NODE_PATH=node_modules node scratch/test_adversarial_oddities_e2e.js
```

### Generated Artifact Locations:
- `docs/screenshots/`: Official documentation screenshots.
- `portal/static/screenshots/`: Assets served statically by the web portal.
- `scratch/screenshots_restored_tabs/`: Real-time audit screenshots across all 16 states.
- `scratch/screenshots_e2e/`: Local scratch artifacts.

---

## ⏱️ 4. Running Performance & Security Benchmarks

### AST ADK Sanitizer Micro-Benchmark
Verifies that key-stripping executes in **under 28 µs** across 10,000 iterations:
```bash
.venv/bin/python skills/ast-sanitizer-benchmark/scripts/benchmark_ast.py
```

### FDA 21 CFR Part 11 Token Cryptography Suite
Verifies normal token creation, 48-hour expiration gates, and cyber-tamper rejection:
```bash
.venv/bin/python skills/gxp-21cfr11-token-verifier/scripts/verify_tokens.py
```

---

## 🔧 5. Operational Troubleshooting

### Problem: `Port 8090 already in use`
**Resolution**: Identify and terminate the lingering process:
```bash
lsof -i :8090
kill -9 <PID>
```

### Problem: `Google Chrome binary not found`
**Resolution**: Verify that signed Google Chrome is installed in the canonical macOS directory:
```bash
ls -la "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

### Problem: `Git index.lock file exists`
**Resolution**: If a previous git process crashed, remove the stale lock file:
```bash
rm -f .git/index.lock
```
