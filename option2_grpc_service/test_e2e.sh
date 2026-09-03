#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

GRPC_PORT=50055
export GRPC_PORT="${GRPC_PORT}"
export GRPC_HOST="127.0.0.1"

echo "=========================================================="
echo " Starting Option 2: a2a.v1 gRPC Service E2E Test"
echo "=========================================================="

echo "Step 1: Compiling Protobufs..."
./generate_protos.sh

echo ""
echo "Step 2: Starting gRPC Server in background on port ${GRPC_PORT}..."
python3 -m server.server &
SERVER_PID=$!

cleanup() {
    echo "Stopping gRPC server (PID: ${SERVER_PID})..."
    kill -9 ${SERVER_PID} 2>/dev/null || true
}
trap cleanup EXIT

sleep 1.5

echo ""
echo "Step 3: Running gRPC Client Demo & Integration Tests..."
python3 -m client.client_example "127.0.0.1:${GRPC_PORT}"

echo ""
echo "=========================================================="
echo " Option 2 a2a.v1 gRPC Service E2E Tests PASSED!"
echo "=========================================================="
