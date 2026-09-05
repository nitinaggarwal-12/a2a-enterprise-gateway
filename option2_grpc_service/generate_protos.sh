#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

PYTHON="${SCRIPT_DIR}/../.venv/bin/python"
if [ ! -f "${PYTHON}" ]; then
    PYTHON="python3"
fi

echo "Compiling Protobuf definitions for a2a.v1..."

mkdir -p a2a/v1
touch a2a/__init__.py
touch a2a/v1/__init__.py

"${PYTHON}" -m grpc_tools.protoc \
    -Iprotos \
    --python_out=. \
    --grpc_python_out=. \
    protos/a2a/v1/a2a.proto

# Fix relative import in generated grpc file if needed
if [ -f "a2a/v1/a2a_pb2_grpc.py" ]; then
    # Ensure package import works seamlessly
    sed -i.bak 's/import a2a_pb2 as a2a__pb2/from . import a2a_pb2 as a2a__pb2/g' a2a/v1/a2a_pb2_grpc.py 2>/dev/null || true
    rm -f a2a/v1/a2a_pb2_grpc.py.bak
fi

echo " Protobuf and gRPC stubs generated successfully in a2a/v1/"
