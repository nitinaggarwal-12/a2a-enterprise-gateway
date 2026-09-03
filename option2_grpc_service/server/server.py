"""Async gRPC Server for Canonical a2a.v1 Service.

Hosts the AIP-127 compliant A2AService over HTTP/2 with native Protobuf framing.
"""

import asyncio
import logging
import os
import sys
from concurrent import futures
import grpc

from a2a.v1 import a2a_pb2_grpc
from .services import A2AServiceImpl

# Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "service":"a2a-grpc-server", "msg":"%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("grpc_server")


async def serve(host: str = "0.0.0.0", port: int = 50051):
    """Start the asynchronous gRPC server."""
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ("grpc.http2.max_pings_without_data", 0),
            ("grpc.keepalive_time_ms", 10000),
            ("grpc.keepalive_timeout_ms", 5000),
        ],
    )

    a2a_pb2_grpc.add_A2AServiceServicer_to_server(A2AServiceImpl(), server)
    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting a2a.v1 gRPC Server listening on {listen_addr}...")
    await server.start()
    logger.info(f" a2a.v1 gRPC Server successfully started on {listen_addr}")

    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Stopping gRPC server gracefully...")
        await server.stop(grace=3.0)


if __name__ == "__main__":
    host = os.environ.get("GRPC_HOST", "0.0.0.0")
    port = int(os.environ.get("GRPC_PORT", "50051"))
    asyncio.run(serve(host=host, port=port))
