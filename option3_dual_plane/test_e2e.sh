#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

echo "=========================================================="
echo " Starting Option 3: Dual-Plane Architecture Simulation"
echo "=========================================================="

python3 run_simulation.py

echo ""
echo "=========================================================="
echo " Option 3 Dual-Plane Architecture Simulation PASSED!"
echo "=========================================================="
