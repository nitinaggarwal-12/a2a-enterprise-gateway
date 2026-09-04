---
name: ast-sanitizer-benchmark
description: >-
  Use this skill whenever benchmarking, profiling, or testing the in-memory AST
  ADK key sanitizer in the Enterprise A2A Gateway. Ensures payload key-stripping
  latency remains under 28 microseconds with zero regex backtracking.
---

# AST Sanitizer Benchmark & Performance Guard

This skill validates the core latency contract of the Enterprise A2A Gateway: in-memory recursive dictionary AST key-stripping must execute in **under 28 µs** for complex biopharma CDISC payloads.

## Key Sanitization Contract
Outbound payloads to external Gemini Enterprise endpoints or A2UI cards must strictly strip:
- `__internal_trace__`
- `adk_internal_context`
- `prompt_injection_flag`
- `raw_system_prompt`
- Any internal keys beginning with `__`

## Execution Steps

### Step 1: Run 10,000-Iteration Benchmark
Execute the automated micro-benchmark using Python's high-resolution `time.perf_counter_ns()`:

```bash
.venv/bin/python skills/ast-sanitizer-benchmark/scripts/benchmark_ast.py
```

### Step 2: Evaluate Latency Budget
- **Target**: Average execution $\le$ 28.00 µs.
- **Warning Threshold**: 28.01 µs – 35.00 µs (investigate recursive depth).
- **Critical Failure**: $> 35.00$ µs (reject build).

### Step 3: Zero-Contamination Verification
Ensure the benchmark output confirms zero prohibited keys survived the pass across nested dictionaries and list structures.
