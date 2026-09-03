#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

source .venv/bin/activate

PORTAL_PORT=8090

echo "=========================================================="
echo " Starting Visual E2E Screenshot Testing Suite"
echo "=========================================================="

echo "Starting Visual Verification Portal on port ${PORTAL_PORT}..."
python3 -m uvicorn portal.app:app --host 127.0.0.1 --port ${PORTAL_PORT} &
PORTAL_PID=$!

cleanup() {
    echo "Stopping portal server (PID: ${PORTAL_PID})..."
    kill -9 ${PORTAL_PID} 2>/dev/null || true
}
trap cleanup EXIT

echo "Waiting for portal to be online..."
for i in {1..20}; do
    if curl -s "http://127.0.0.1:${PORTAL_PORT}/api/health/all" | grep -q "online"; then
        echo " Portal is healthy and ready on http://127.0.0.1:${PORTAL_PORT}!"
        break
    fi
    sleep 0.5
done

echo ""
echo "Executing Puppeteer headless browser automated test run..."
node scratch/run_e2e_screenshots.js

echo ""
echo "=========================================================="
echo " Visual E2E Verification Complete! Screenshots captured."
echo "=========================================================="
