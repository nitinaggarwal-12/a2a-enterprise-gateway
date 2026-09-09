"""Honest local micro-benchmark suite for A2A gateway primitives.

This file measures ONLY functions executed in this process. It intentionally
does not invent throughput, cold-start, memory, regulatory-risk, or production
SLA values for architectures that were not exercised.

Use benchmarks/live_real_load_test.py for local socket integration tests and a
separate deployed load-test job for staging/production measurements.
"""

from datetime import datetime, timezone
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from option1_cloud_run_gateway.app.sanitizer import sanitize_a2a_envelope
from option1_cloud_run_gateway.app.security import create_state_token, verify_state_token


def percentile(values: list[float], pct: float) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * pct)))
    return ordered[index]


def benchmark_sanitizer(iterations: int = 5000) -> Dict[str, Any]:
    contaminated = {
        "jsonrpc": "2.0",
        "method": "SendMessage",
        "adk_metadata": {"trace": "private"},
        "__internal_trace__": "private",
        "system_override": "private",
        "params": {
            "message": {
                "messageId": "bench-message",
                "role": "ROLE_USER",
                "parts": [{"text": "hello"}],
                "metadata": {
                    "access_token": "should-not-survive",
                    "__adk_trace": "should-not-survive",
                },
            }
        },
        "id": "bench-1",
    }

    latencies_us: list[float] = []
    leak_failures = 0
    for _ in range(iterations):
        start = time.perf_counter_ns()
        cleaned = sanitize_a2a_envelope(contaminated)
        latencies_us.append((time.perf_counter_ns() - start) / 1000.0)

        serialized = json.dumps(cleaned).lower()
        if any(
            marker in serialized
            for marker in (
                "adk_metadata",
                "__internal_trace__",
                "system_override",
                "should-not-survive",
            )
        ):
            leak_failures += 1

    mean_us = statistics.fmean(latencies_us)
    return {
        "measurementType": "local_in_process_microbenchmark",
        "iterations": iterations,
        "p50_us": round(percentile(latencies_us, 0.50), 3),
        "p95_us": round(percentile(latencies_us, 0.95), 3),
        "p99_us": round(percentile(latencies_us, 0.99), 3),
        "mean_us": round(mean_us, 3),
        "operations_per_second_equivalent": round(1_000_000 / mean_us, 1),
        "demo_corpus_leak_failures": leak_failures,
        "demo_corpus_pass_rate_pct": round((iterations - leak_failures) * 100 / iterations, 4),
        "scopeWarning": (
            "Pass rate applies only to this finite adversarial corpus. "
            "It is not a guarantee of zero leakage or regulatory compliance."
        ),
    }


def benchmark_state_token_crypto(iterations: int = 5000) -> Dict[str, Any]:
    sample_state = {
        "taskId": "task-local-bench",
        "decision": "APPROVED",
        "approverSub": "bench-subject",
    }
    seal_us: list[float] = []
    verify_us: list[float] = []

    for _ in range(iterations):
        start = time.perf_counter_ns()
        token = create_state_token(sample_state)
        seal_us.append((time.perf_counter_ns() - start) / 1000.0)

        start = time.perf_counter_ns()
        verify_state_token(token)
        verify_us.append((time.perf_counter_ns() - start) / 1000.0)

    return {
        "measurementType": "local_in_process_microbenchmark",
        "iterations": iterations,
        "seal_p50_us": round(percentile(seal_us, 0.50), 3),
        "seal_p95_us": round(percentile(seal_us, 0.95), 3),
        "verify_p50_us": round(percentile(verify_us, 0.50), 3),
        "verify_p95_us": round(percentile(verify_us, 0.95), 3),
        "scopeWarning": "Cryptographic primitive timing is not end-to-end gateway latency.",
    }


def build_report() -> Dict[str, Any]:
    return {
        "benchmark_timestamp": datetime.now(timezone.utc).isoformat(),
        "evidence": {
            "environment": "local_process",
            "productionMeasurement": False,
            "regulatoryValidation": False,
            "source": "benchmarks/run_kpi_benchmarks.py",
        },
        "metrics": {
            "option1_gateway_primitives": {
                "status": "MEASURED_LOCALLY",
                "sanitizer": benchmark_sanitizer(),
                "state_token_crypto": benchmark_state_token_crypto(),
            },
            "option2_grpc": {
                "status": "NOT_MEASURED_BY_THIS_SUITE",
                "reason": "No Option 2 service is started by this micro-benchmark.",
            },
            "option3_dual_plane": {
                "status": "NOT_MEASURED_BY_THIS_SUITE",
                "reason": "No Option 3 service is started by this micro-benchmark.",
            },
        },
    }


def main() -> None:
    report = build_report()
    out = ROOT_DIR / "benchmarks" / "benchmark_results.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote local micro-benchmark artifact: {out}")


if __name__ == "__main__":
    main()
