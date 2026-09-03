#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

source .venv/bin/activate

echo "================================================================================"
echo " Enterprise ENTERPRISE AGENT INTEGRATION ARCHITECTURE - MASTER TEST SUITE"
echo " Evaluating Option 1, Option 2, and Option 3 End-to-End"
echo "================================================================================"

echo ""
echo ">>> [1/3] EXECUTING OPTION 1: CLOUD RUN INTERCEPTOR GATEWAY (FAST TRACK) <<<"
cd option1_cloud_run_gateway
pytest tests/ -v
./test_e2e.sh
cd ..

echo ""
echo ">>> [2/3] EXECUTING OPTION 2: TRANSPORT PIVOT TO a2a.v1 gRPC <<<"
cd option2_grpc_service
./test_e2e.sh
cd ..

echo ""
echo ">>> [3/3] EXECUTING OPTION 3: OUTSIDE-IN DUAL-PLANE PLATFORM DEMARCATION <<<"
cd option3_dual_plane
./test_e2e.sh
cd ..

echo ""
echo "================================================================================"
echo " ALL 3 OPTIONS COMPILED, EXECUTED, AND VERIFIED END-TO-END WITH ZERO FAILURES!"
echo "================================================================================"
