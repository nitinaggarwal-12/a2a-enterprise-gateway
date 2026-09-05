#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${VIRTUAL_ENV:-.venv}/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo " Compiling Google A2A v1.0.0 Protobuf definitions..."
"$PYTHON_BIN" -m grpc_tools.protoc \
  -Ioption2_grpc_service/protos \
  --python_out=option2_grpc_service \
  --grpc_python_out=option2_grpc_service \
  option2_grpc_service/protos/a2a/v1/a2a.proto

echo " Successfully compiled a2a_pb2.py and a2a_pb2_grpc.py into option2_grpc_service/a2a/v1/"
