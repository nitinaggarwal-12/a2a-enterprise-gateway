# Operations Runbook

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export APP_ENV=development
export ALLOW_DEV_AUTH=true
export ENABLE_LAB_ENDPOINTS=true
export JWT_SECRET='local-development-secret-with-at-least-32-characters'

python -m uvicorn portal.app:app --host 127.0.0.1 --port 8090
```

Health:

```bash
curl http://127.0.0.1:8090/api/health/all
```

`/api/health/all` reports `unknown` for services whose health URL is not configured; it never manufactures an online status.

## Gateway production configuration

Review at least:

```bash
APP_ENV=production
ALLOW_DEV_AUTH=false
ENABLE_LAB_ENDPOINTS=false
JWT_SECRET=<managed secret>
EXPECTED_AUDIENCE=<gateway OIDC audience>
REDIS_URL=<durable atomic replay store>

DOWNSTREAM_AGENT_URL=https://...
DOWNSTREAM_ID_TOKEN_AUDIENCE=https://...

WEBHOOK_ALLOWED_HOSTS=callback.example.internal
CORS_ALLOWED_ORIGINS=https://admin.example.com
TRUST_PROXY_HEADERS=false
```

If trusted forwarding headers are required, set `TRUST_PROXY_HEADERS=true` only when an upstream proxy is guaranteed to remove caller-supplied forwarding headers.

## Tests

```bash
pytest -q
python -m compileall option1_cloud_run_gateway option2_grpc_service option3_dual_plane portal a2a_sdk
```

The test suite explicitly opts into mock development auth in `option1_cloud_run_gateway/tests/conftest.py`. Application defaults remain fail-closed.

## A2A v1 smoke test

1. Retrieve the Agent Card:

```bash
curl http://127.0.0.1:8080/.well-known/agent-card.json
```

2. Call the v1 JSON-RPC binding with an authenticated token and:

```text
A2A-Version: 1.0
```

The gateway rejects unsupported versions rather than silently accepting `1.0.0` or a legacy version on the v1 interface.

## Benchmarks

```bash
python benchmarks/run_kpi_benchmarks.py
python benchmarks/live_real_load_test.py
```

The first is an in-process microbenchmark. The second starts local loopback processes.

Neither is a production load test. Do not present local results as Railway/Cloud Run SLA evidence.

A deployed benchmark must record at least:

- commit SHA
- environment/service revision
- region
- instance/concurrency configuration
- dependency versions
- timestamp
- payload corpus
- sample size/concurrency
- p50/p95/p99
- raw result artifact
- whether each metric was measured, estimated, or unavailable

## Lab signing APIs

The following are experimental and disabled unless `ENABLE_LAB_ENDPOINTS=true`:

- swarm registration resources
- signature create/verify/receipt resources
- demo dossier resources
- replay-registry reset
- benchmark worker dispatch

They require authentication even when lab mode is enabled.

Unknown IDs return 404. They must never be interpreted as valid records.

## Replay-store failures

In staging/production, failure to configure or reach the distributed JTI store is a security failure. Approval actions return 503 instead of falling back to local memory.

Investigate the Redis/Memorystore connection before retrying.

## Downstream authentication failures

If `DOWNSTREAM_ID_TOKEN_AUDIENCE` is set and ADC cannot mint an ID token, proxy calls fail with 503. Verify:

- workload identity/ADC availability
- target audience
- IAM permission
- downstream service authentication configuration

Do not work around this by forwarding the caller's bearer token.

## Webhook rejection

If a callback is rejected, verify:

- HTTPS
- exact hostname in `WEBHOOK_ALLOWED_HOSTS`
- DNS resolution
- target is not private/link-local/metadata/special-use unless an approved architecture intentionally supports it

For private callbacks, use an architecture with an explicit private egress path rather than weakening the public SSRF policy.

## Incident guidance

For suspected credential leakage:

1. disable affected endpoint/deployment
2. rotate the relevant secret/key
3. remove or revoke downstream credentials
4. inspect gateway/downstream logs
5. invalidate/reconcile pending approvals where required
6. preserve evidence
7. follow the organization's incident and regulated-change procedures

Never paste secrets or patient data into a public GitHub issue.
