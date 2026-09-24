#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

source .venv/bin/activate
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
export APP_ENV="development"
export ALLOW_DEV_AUTH="true"
export PUPPETEER_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"

echo "================================================================================"
echo " ENTERPRISE A2A GATEWAY - CANONICAL MASTER TEST SUITE"
echo " Evaluating Option 1 Cloud Run Interceptor Gateway & Portal Quality Gate"
echo "================================================================================"

echo ""
echo ">>> [1/3] EXECUTING OPTION 1: PYTHON UNIT & SECURITY TEST SUITE (123 TESTS) <<<"
cd option1_cloud_run_gateway
pytest tests/ -v
cd ..

echo ""
echo ">>> [2/3] EXECUTING OPTION 1: CLI END-TO-END VERIFICATION HARNESS <<<"
cd option1_cloud_run_gateway
./test_e2e.sh
cd ..

echo ""
echo ">>> [3/3] EXECUTING COMPREHENSIVE FRONTEND PORTAL E2E QUALITY GATE <<<"
NODE_PATH=node_modules node scratch/test_all_restored_tabs.js
NODE_PATH=node_modules node scratch/test_phase3_e2e.js

echo ""
echo "================================================================================"
echo " OPTION 1 CLOUD RUN GATEWAY + MULTIMODAL VERIFICATION PORTAL VERIFIED (0 ERRORS)!"
echo "================================================================================"

