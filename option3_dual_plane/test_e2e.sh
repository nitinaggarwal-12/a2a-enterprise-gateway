#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

PYTHON="${SCRIPT_DIR}/../.venv/bin/python"
if [ ! -f "${PYTHON}" ]; then
    PYTHON="python3"
fi

echo "=========================================================="
echo " Starting Option 3: Dual-Plane Architecture Simulation"
echo "=========================================================="

"${PYTHON}" run_simulation.py

echo ""
echo "=========================================================="
echo " Option 3 Dual-Plane Architecture Simulation PASSED!"
echo "=========================================================="
