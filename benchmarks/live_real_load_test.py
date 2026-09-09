"""Local socket integration benchmark suite.

This suite starts repository services on loopback and measures those local
processes. Results are NOT Cloud Run/Railway/production measurements and do not
constitute regulatory validation.

Executes actual socket connections against locally started instances of:
- Option 1: Cloud Run Gateway (HTTP/1.1 REST + SSE)
- Option 2: a2a.v1 gRPC Server (HTTP/2 Binary RPC)
- Option 3: Dual-Plane Architecture (REST + Direct Vertex AI loop)

Measures local-process observations:
- Process startup / cold-start time (ms)
- Resident Set Size (RSS) memory consumption (MB)
- E2E Network round-trip latencies over TCP socket (p50, p90, p95, p99 in ms)
- Wire payload sizes in bytes
- Real throughput (requests/sec) under concurrency
- strict demo schema acceptance/rejection for a finite adversarial corpus
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import statistics
from datetime import datetime, timezone
import psutil
from pathlib import Path
from typing import Any, Dict, List
import httpx
import grpc
from google.protobuf import struct_pb2
from pydantic import BaseModel, ConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "option1_cloud_run_gateway"))
sys.path.insert(0, str(ROOT_DIR / "option2_grpc_service"))
sys.path.insert(0, str(ROOT_DIR / "option3_dual_plane"))

from option1_cloud_run_gateway.app.sanitizer import sanitize_a2a_envelope
from option2_grpc_service.a2a.v1 import a2a_pb2, a2a_pb2_grpc


# Finite demo strict schema used only to exercise undeclared-field rejection.
class StrictDemoClinicalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")  # Strictly rejects ANY undeclared keys!
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: str


async def measure_server_cold_start(
    command: List[str],
    health_check_fn,
    timeout: float = 10.0,
    env: Dict[str, str] | None = None,
):
    """Start a local server process and measure until its loopback health check responds."""
    t_start = time.perf_counter()
    proc = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(ROOT_DIR),
        env=env,
    )
    is_ready = False
    while (time.perf_counter() - t_start) < timeout:
        if await health_check_fn():
            is_ready = True
            break
        await asyncio.sleep(0.01)
    t_end = time.perf_counter()

    if not is_ready:
        proc.kill()
        raise RuntimeError(f"Server failed to start within {timeout}s: {' '.join(command)}")

    cold_start_ms = round((t_end - t_start) * 1000.0, 2)
    ps_proc = psutil.Process(proc.pid)
    idle_memory_mb = round(ps_proc.memory_info().rss / (1024 * 1024), 2)

    return proc, ps_proc, cold_start_ms, idle_memory_mb


async def main():
    print("=" * 80)
    print("🔬 RUNNING LOCAL SOCKET INTEGRATION BENCHMARKS (NOT PRODUCTION)")
    print("=" * 80)

    results = {}

    # =========================================================================
    # 1. OPTION 1 BENCHMARKS (Cloud Run Gateway)
    # =========================================================================
    print("\n[1/3] Benchmarking Option 1: Cloud Run Interceptor Gateway...")
    opt1_port = 8086
    opt1_url = f"http://127.0.0.1:{opt1_port}"

    async def opt1_health():
        try:
            async with httpx.AsyncClient(timeout=0.2) as c:
                r = await c.get(f"{opt1_url}/healthz")
                return r.status_code == 200
        except Exception:
            return False

    opt1_cmd = [
        sys.executable, "-m", "uvicorn",
        "option1_cloud_run_gateway.app.main:app",
        "--host", "127.0.0.1", "--port", str(opt1_port),
        "--log-level", "error",
    ]

    opt1_env = os.environ.copy()
    opt1_env["APP_ENV"] = "development"
    opt1_env["ALLOW_DEV_AUTH"] = "true"
    opt1_env["ENABLE_LAB_ENDPOINTS"] = "false"
    opt1_env["JWT_SECRET"] = "local-benchmark-only-secret-with-at-least-32-characters"
    opt1_proc, opt1_ps, opt1_cold_start_ms, opt1_idle_mb = await measure_server_cold_start(
        opt1_cmd, opt1_health, env=opt1_env
    )
    print(f"   Option 1 Cold Start: {opt1_cold_start_ms} ms | Idle RSS Memory: {opt1_idle_mb} MB")

    # Measure 500 Real HTTP/1.1 Socket Round-Trips with Contaminated Payload
    contaminated_req = {
        "jsonrpc": "2.0",
        "method": "a2a.tasks.send",
        "adk_metadata": {"model": "gemini-1.5-pro", "system_prompt_hash": "a1b2c3d4e5"},
        "_adk": {"envelope": "alpha", "trace_id": "goog-trace-999"},
        "ge_context": {"session": "ge-sess-44321"},
        "params": {
            "taskId": "task-bench-live-01",
            "studyId": "MK-3475-087",
            "cohort": "Cohort-B",
            "__adk_internal": "secret-leakage",
        },
        "id": "req-bench-01",
    }

    raw_req_bytes = len(json.dumps(contaminated_req).encode("utf-8"))

    opt1_latencies_ms = []
    opt1_action_latencies_ms = []
    strict_schema_rejected_raw = False
    strict_schema_accepted_sanitized = False

    try:
        StrictDemoClinicalPayload.model_validate(contaminated_req)
    except Exception:
        strict_schema_rejected_raw = True

    sanitized_for_validation = sanitize_a2a_envelope(contaminated_req)
    StrictDemoClinicalPayload.model_validate(sanitized_for_validation)
    strict_schema_accepted_sanitized = True

    sample_state_token = None

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Measure 500 live task requests
        t_start_all = time.perf_counter()
        for i in range(500):
            t0 = time.perf_counter()
            resp = await client.post(
                f"{opt1_url}/a2a/tasks",
                json=contaminated_req,
                headers={"Authorization": "Bearer mock-dev-token", "X-Google-ADK-Trace": "goog-header-1"},
            )
            t1 = time.perf_counter()
            assert resp.status_code == 200
            opt1_latencies_ms.append((t1 - t0) * 1000.0)

            if i == 0:
                resp_json = resp.json()
                sample_state_token = resp_json["result"]["artifact"]["a2ui"]["actions"][0]["stateToken"]
                # Token captured only for size reporting; replay benchmark uses unique tokens.

        t_end_all = time.perf_counter()
        opt1_throughput_rps = round(500.0 / (t_end_all - t_start_all), 1)

        # Pre-generate unique state tokens through the running gateway. Reusing one
        # token would correctly trigger the replay guard after the first action.
        action_tokens = []
        for i in range(500):
            token_req = json.loads(json.dumps(contaminated_req))
            token_req["id"] = f"token-prep-{i}"
            token_req["params"]["taskId"] = f"task-action-{i}"
            token_resp = await client.post(
                f"{opt1_url}/a2a/tasks",
                json=token_req,
                headers={"Authorization": "Bearer mock-dev-token"},
            )
            assert token_resp.status_code == 200
            action_tokens.append(
                token_resp.json()["result"]["artifact"]["a2ui"]["actions"][0]["stateToken"]
            )

        for i, state_token in enumerate(action_tokens):
            action_req = {
                "jsonrpc": "2.0",
                "method": "a2a.ui.action",
                "params": {"stateToken": state_token},
                "id": f"action-bench-{i}",
            }
            t0 = time.perf_counter()
            resp = await client.post(
                f"{opt1_url}/a2a/ui/action",
                json=action_req,
                headers={"Authorization": "Bearer mock-dev-token"},
            )
            t1 = time.perf_counter()
            assert resp.status_code == 200
            opt1_action_latencies_ms.append((t1 - t0) * 1000.0)

        # Explicitly prove replay is rejected.
        replay_resp = await client.post(
            f"{opt1_url}/a2a/ui/action",
            json={
                "jsonrpc": "2.0",
                "method": "a2a.ui.action",
                "params": {"stateToken": action_tokens[0]},
                "id": "replay-check",
            },
            headers={"Authorization": "Bearer mock-dev-token"},
        )
        assert replay_resp.status_code == 409

    opt1_peak_mb = round(opt1_ps.memory_info().rss / (1024 * 1024), 2)
    opt1_proc.terminate()

    results["option1"] = {
        "cold_start_ms": opt1_cold_start_ms,
        "idle_memory_mb": opt1_idle_mb,
        "peak_memory_mb": opt1_peak_mb,
        "task_dispatch_latency_p50_ms": round(statistics.median(opt1_latencies_ms), 3),
        "task_dispatch_latency_p90_ms": round(statistics.quantiles(opt1_latencies_ms, n=10)[8], 3),
        "task_dispatch_latency_p95_ms": round(statistics.quantiles(opt1_latencies_ms, n=20)[18], 3),
        "task_dispatch_latency_p99_ms": round(statistics.quantiles(opt1_latencies_ms, n=100)[98], 3),
        "ui_action_latency_p50_ms": round(statistics.median(opt1_action_latencies_ms), 3),
        "local_sequential_throughput_rps": opt1_throughput_rps,
        "wire_payload_request_bytes": raw_req_bytes,
        "hmac_state_token_bytes": len(sample_state_token.encode("utf-8")),
        "strict_demo_schema_rejected_raw_payload": strict_schema_rejected_raw,
        "strict_demo_schema_accepted_sanitized_payload": strict_schema_accepted_sanitized,
        "replay_guard_verified": True,
        "validation_scope": "finite local demo corpus; not GxP/Part 11 validation",
    }

    # =========================================================================
    # 2. OPTION 2 BENCHMARKS (a2a.v1 gRPC HTTP/2 Server)
    # =========================================================================
    print("\n[2/3] Benchmarking Option 2: a2a.v1 gRPC Service...")
    opt2_port = 50058
    opt2_target = f"127.0.0.1:{opt2_port}"

    async def opt2_health():
        try:
            async with grpc.aio.insecure_channel(opt2_target) as ch:
                stub = a2a_pb2_grpc.A2AServiceStub(ch)
                # Call with quick timeout
                await asyncio.wait_for(ch.channel_ready(), timeout=0.1)
                return True
        except Exception:
            return False

    opt2_env = os.environ.copy()
    opt2_env["GRPC_PORT"] = str(opt2_port)
    opt2_env["GRPC_HOST"] = "127.0.0.1"

    opt2_cmd = [sys.executable, "-m", "option2_grpc_service.server.server"]

    t0_grpc = time.perf_counter()
    opt2_proc = subprocess.Popen(opt2_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(ROOT_DIR), env=opt2_env)
    
    # Wait for channel readiness
    async with grpc.aio.insecure_channel(opt2_target) as ch:
        await ch.channel_ready()
    t1_grpc = time.perf_counter()
    opt2_cold_start_ms = round((t1_grpc - t0_grpc) * 1000.0, 2)
    opt2_ps = psutil.Process(opt2_proc.pid)
    opt2_idle_mb = round(opt2_ps.memory_info().rss / (1024 * 1024), 2)
    print(f"   Option 2 Cold Start: {opt2_cold_start_ms} ms | Idle RSS Memory: {opt2_idle_mb} MB")

    # Measure 500 Real gRPC Socket RPC Calls over HTTP/2 Channel
    opt2_latencies_ms = []
    grpc_msg_bytes = 0

    async with grpc.aio.insecure_channel(opt2_target) as channel:
        stub = a2a_pb2_grpc.A2AServiceStub(channel)
        params = struct_pb2.Struct()
        params.update({"studyId": "MK-3475-087", "cohort": "Cohort-B"})
        req = a2a_pb2.ExecuteTaskRequest(task_id="bench-task-grpc-01", parameters=params)
        grpc_msg_bytes = len(req.SerializeToString())

        t_start_all = time.perf_counter()
        for _ in range(500):
            t0 = time.perf_counter()
            response: a2a_pb2.Task = await stub.ExecuteTask(req)
            t1 = time.perf_counter()
            opt2_latencies_ms.append((t1 - t0) * 1000.0)
        t_end_all = time.perf_counter()
        opt2_throughput_rps = round(500.0 / (t_end_all - t_start_all), 1)

    opt2_peak_mb = round(opt2_ps.memory_info().rss / (1024 * 1024), 2)
    opt2_proc.terminate()

    results["option2"] = {
        "cold_start_ms": opt2_cold_start_ms,
        "idle_memory_mb": opt2_idle_mb,
        "peak_memory_mb": opt2_peak_mb,
        "task_dispatch_latency_p50_ms": round(statistics.median(opt2_latencies_ms), 3),
        "task_dispatch_latency_p90_ms": round(statistics.quantiles(opt2_latencies_ms, n=10)[8], 3),
        "task_dispatch_latency_p95_ms": round(statistics.quantiles(opt2_latencies_ms, n=20)[18], 3),
        "task_dispatch_latency_p99_ms": round(statistics.quantiles(opt2_latencies_ms, n=100)[98], 3),
        "local_sequential_throughput_rps": opt2_throughput_rps,
        "wire_payload_request_bytes": grpc_msg_bytes,
        "transport_layer": "gRPC over HTTP/2 (Binary Protobuf)",
        "client_ingress_requirement": "gRPC-Web / Envoy Ingress Bridge required",
    }

    # =========================================================================
    # 3. OPTION 3 BENCHMARKS (Dual-Plane Demarcation)
    # =========================================================================
    print("\n[3/3] Benchmarking Option 3: Dual-Plane Sovereign Architecture...")
    bridge_port = 8096
    ge_port = 8097
    bridge_url = f"http://127.0.0.1:{bridge_port}"
    ge_url = f"http://127.0.0.1:{ge_port}"

    async def opt3_health():
        try:
            async with httpx.AsyncClient(timeout=0.2) as client:
                response = await client.get(f"{bridge_url}/healthz")
                return response.status_code == 200
        except Exception:
            return False

    opt3_env = os.environ.copy()
    opt3_env["BRIDGE_PORT"] = str(bridge_port)
    opt3_env["GE_INBOUND_PORT"] = str(ge_port)
    opt3_env["BRIDGE_SERVICE_URL"] = bridge_url
    opt3_env["GE_INBOUND_URL"] = ge_url

    opt3_cmd = [
        sys.executable, "-m", "uvicorn",
        "option3_dual_plane.ui_bridge.bridge_service:app",
        "--host", "127.0.0.1", "--port", str(bridge_port),
        "--log-level", "error",
    ]

    opt3_proc, opt3_ps, opt3_cold_start_ms, opt3_idle_mb = await measure_server_cold_start(
        opt3_cmd, opt3_health, env=opt3_env
    )
    print(f"   Option 3 Cold Start: {opt3_cold_start_ms} ms | Idle RSS Memory: {opt3_idle_mb} MB")

    # Measure 100 Real Plane 1 + Plane 2 Round-Trips
    opt3_latencies_ms = []
    engine = VertexAIClinicalEngine()

    async with httpx.AsyncClient(timeout=10.0) as client:
        t_start_all = time.perf_counter()
        for _ in range(100):
            t0 = time.perf_counter()
            # 1. Plane 1 Execution
            analysis = await engine.execute_clinical_reasoning_loop("MK-3475-087", "Cohort-B")
            # 2. Handshake to Plane 2 Bridge
            bridge_resp = await client.post(
                f"{bridge_url}/api/v1/bridge/dispatch-approval",
                json={
                    "studyId": analysis.study_id,
                    "cohort": analysis.test_cohort,
                    "variancePct": analysis.variance_pct,
                    "clinicalFindings": analysis.clinical_findings,
                    "recommendedAmendment": analysis.recommended_protocol_amendment,
                },
            )
            assert bridge_resp.status_code == 200
            t1 = time.perf_counter()
            opt3_latencies_ms.append((t1 - t0) * 1000.0)
        t_end_all = time.perf_counter()
        opt3_throughput_rps = round(100.0 / (t_end_all - t_start_all), 1)

    opt3_peak_mb = round(opt3_ps.memory_info().rss / (1024 * 1024), 2)
    opt3_proc.terminate()

    results["option3"] = {
        "cold_start_ms": opt3_cold_start_ms,
        "idle_memory_mb": opt3_idle_mb,
        "peak_memory_mb": opt3_peak_mb,
        "end_to_end_pipeline_latency_p50_ms": round(statistics.median(opt3_latencies_ms), 3),
        "end_to_end_pipeline_latency_p95_ms": round(statistics.quantiles(opt3_latencies_ms, n=20)[18], 3),
        "local_sequential_throughput_rps": opt3_throughput_rps,
        "data_isolation_claim": "NOT_MEASURED_BY_THIS_LOCAL_TEST",
    }

    # Print clean summary
    print("\n" + "=" * 80)
    print(" LOCAL SOCKET TEST RESULTS SUMMARY (LOOPBACK ONLY)")
    print("=" * 80)
    print(json.dumps(results, indent=2))

    report = {
        "benchmark_timestamp": datetime.now(timezone.utc).isoformat(),
        "evidence": {
            "environment": "local_loopback_processes",
            "productionMeasurement": False,
            "regulatoryValidation": False,
            "source": "benchmarks/live_real_load_test.py",
        },
        "metrics": results,
    }

    out_file = ROOT_DIR / "benchmarks" / "live_empirical_results.json"
    out_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\n Saved local integration metrics to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
