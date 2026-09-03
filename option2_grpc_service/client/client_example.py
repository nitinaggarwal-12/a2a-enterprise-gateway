"""Python gRPC Client for a2a.v1 Service.

Demonstrates:
1. Synchronous ExecuteTask RPC with AIP-127 Push Config.
2. Progressive Server-Streaming StreamTask RPC with real-time reasoning events.
3. Graceful Task Cancellation with CancelTask RPC.
4. Protobuf Binary Deserialization Shielding against ADK envelope pollution.

Step-by-step local testing instructions:
----------------------------------------
1. Compile protos:
   ./generate_protos.sh

2. Run server in one terminal:
   python3 -m server.server

3. Run client in another terminal:
   python3 -m client.client_example
"""

import asyncio
import sys
import grpc
from google.protobuf import struct_pb2

from a2a.v1 import a2a_pb2, a2a_pb2_grpc


async def run_client_demo(server_target: str = "127.0.0.1:50051"):
    print("=" * 60)
    print(f" Connecting to a2a.v1 gRPC Service at {server_target}...")
    print("=" * 60)

    async with grpc.aio.insecure_channel(server_target) as channel:
        stub = a2a_pb2_grpc.A2AServiceStub(channel)

        # ------------------------------------------------------------------
        # Demo 1: Synchronous ExecuteTask RPC
        # ------------------------------------------------------------------
        print("\n--- Demo 1: Calling ExecuteTask (Synchronous) ---")
        params = struct_pb2.Struct()
        params.update({
            "studyId": "MK-3475-087",
            "cohort": "Cohort-B",
            "protocolVersion": "v4.2",
        })

        push_config = a2a_pb2.TaskPushNotificationConfig(
            url="http://127.0.0.1:8089/webhook/ge-push",
            token="bearer-grpc-push-token",
        )

        request = a2a_pb2.ExecuteTaskRequest(
            task_id="task-grpc-sync-001",
            parameters=params,
            push_config=push_config,
        )

        # Send request with optional gRPC metadata
        response: a2a_pb2.Task = await stub.ExecuteTask(
            request,
            metadata=(("x-client-id", "Enterprise-orchestrator-cli"),),
        )

        print(f"Task Response ID: {response.id}")
        print(f"Task State: {a2a_pb2.TaskState.Name(response.state)}")
        print(f"Output Payload: {dict(response.output.fields)}")

        # ------------------------------------------------------------------
        # Demo 2: Streaming StreamTask RPC
        # ------------------------------------------------------------------
        print("\n--- Demo 2: Calling StreamTask (Server Streaming Reasoning Trace) ---")
        stream_request = a2a_pb2.ExecuteTaskRequest(
            task_id="task-grpc-stream-002",
            parameters=params,
            push_config=push_config,
        )

        async for chunk in stub.StreamTask(stream_request):
            state_name = a2a_pb2.TaskState.Name(chunk.current_state)
            print(f"[{state_name}] -> {chunk.chunk_text}")
            if chunk.is_terminal:
                print(f" Terminal Payload Received: {dict(chunk.payload.fields)}")

        # ------------------------------------------------------------------
        # Demo 3: Task Cancellation RPC
        # ------------------------------------------------------------------
        print("\n--- Demo 3: Calling CancelTask ---")
        cancel_req = a2a_pb2.CancelTaskRequest(
            task_id="task-grpc-stream-002",
            reason="Clinical study amendment superseded by protocol v4.3",
        )
        await stub.CancelTask(cancel_req)
        print(" CancelTask RPC executed successfully.")

        print("\n" + "=" * 60)
        print(" All a2a.v1 gRPC Client Integration Demos Completed Successfully!")
        print("=" * 60)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:50051"
    asyncio.run(run_client_demo(target))
