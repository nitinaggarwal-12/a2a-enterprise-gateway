"""Async gRPC Server for Canonical a2a.v1 Service.

Hosts the AIP-127 compliant A2AService over HTTP/2 with native Protobuf framing,
supporting mutual TLS (mTLS) and Bearer token authentication.
"""

import asyncio
import logging
import os
import sys
from concurrent import futures
from typing import Optional, Tuple
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


class AuthInterceptor(grpc.aio.ServerInterceptor):
    """Server interceptor validating Bearer token / OIDC credentials."""

    def __init__(self, expected_secret: Optional[str] = None):
        self.expected_secret = expected_secret or os.getenv("A2A_GRPC_AUTH_TOKEN", "mock-dev-token")
        self.require_auth = os.getenv("A2A_GRPC_REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")

    async def intercept_service(self, continuation, handler_call_details):
        if not self.require_auth:
            return await continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        auth_header = metadata.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            def abort(request, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing or invalid Bearer authorization metadata")
            return grpc.unary_unary_rpc_method_handler(abort)

        token = auth_header.split(" ", 1)[1].strip()
        if self.expected_secret and token != self.expected_secret:
            def abort(request, context):
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid gRPC Bearer authentication token")
            return grpc.unary_unary_rpc_method_handler(abort)

        return await continuation(handler_call_details)


def load_ssl_credentials() -> Tuple[Optional[grpc.ServerCredentials], bool]:
    """Load SSL server credentials for TLS / mTLS if configured in environment."""
    cert_path = os.getenv("GRPC_TLS_CERT_PATH") or os.getenv("GRPC_SSL_CERT_PATH")
    key_path = os.getenv("GRPC_TLS_KEY_PATH") or os.getenv("GRPC_SSL_KEY_PATH")
    client_ca_path = os.getenv("GRPC_CLIENT_CA_PATH") or os.getenv("GRPC_CA_CERT_PATH")

    if not cert_path or not key_path:
        return None, False

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logger.warning(f"[gRPC Server] TLS cert/key paths specified but not found: {cert_path}, {key_path}")
        return None, False

    with open(key_path, "rb") as f:
        private_key = f.read()
    with open(cert_path, "rb") as f:
        cert_chain = f.read()

    root_certs = None
    require_client_auth = False
    if client_ca_path and os.path.exists(client_ca_path):
        with open(client_ca_path, "rb") as f:
            root_certs = f.read()
        require_client_auth = True
        logger.info("[gRPC Server] mTLS Mutual Authentication enabled (client certificate required).")

    creds = grpc.ssl_server_credentials(
        [(private_key, cert_chain)],
        root_certificates=root_certs,
        require_client_auth=require_client_auth,
    )
    return creds, require_client_auth


async def serve(host: str = "0.0.0.0", port: int = 50051):
    """Start the asynchronous gRPC server."""
    interceptors = [AuthInterceptor()]

    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=interceptors,
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

    ssl_creds, is_mtls = load_ssl_credentials()
    if ssl_creds:
        server.add_secure_port(listen_addr, ssl_creds)
        logger.info(f"Starting secure a2a.v1 gRPC Server ({'mTLS' if is_mtls else 'TLS'}) listening on {listen_addr}...")
    else:
        server.add_insecure_port(listen_addr)
        logger.info(f"Starting a2a.v1 gRPC Server (insecure development) listening on {listen_addr}...")

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
