# A2A Enterprise Gateway

An enterprise policy gateway and interoperability lab for Agent-to-Agent (A2A) integrations.

> **Validation status:** this repository is a reference implementation and demo environment. It is **not** a regulatory certification, a production SLA, a claim of zero data leakage, or evidence that a deployment complies with FDA 21 CFR Part 11, GxP, HIPAA, GAMP 5, or another regulated framework. Those outcomes require deployment-specific controls, validation, operating procedures, evidence, and accountable owners.

## What is implemented

### Standards-facing A2A v1.0 interface

The gateway exposes:

- `GET /.well-known/agent-card.json`
- `POST /a2a/v1`
- `A2A-Version: 1.0` negotiation
- JSON-RPC methods `SendMessage`, `GetTask`, `ListTasks`, and `CancelTask`
- explicit unsupported-operation errors for capabilities the Agent Card does not advertise
- authenticated routing through Google OIDC

The legacy clinical-demo endpoints remain separate from the standards-facing interface.

### Policy boundary

The Option 1 gateway applies a defensive normalization layer before forwarding data:

- removes known ADK/vendor orchestration metadata
- removes obvious credential-bearing fields
- strips caller `Authorization`, cookies, API keys, forwarding headers, and hop-by-hop headers
- restricts the top-level JSON-RPC envelope
- sanitizes JSON Server-Sent Events instead of forwarding raw stream chunks
- rejects opaque non-JSON downstream responses on the policy gateway
- supports exact production webhook host allowlists
- blocks private/link-local/cloud-metadata webhook targets
- can mint a destination-specific downstream Google ID token using Application Default Credentials

This is a defense-in-depth filter, not a universal DLP guarantee. Production deployments should add tenant-specific schema validation, Cloud DLP/content classification where required, and explicit data-egress policy.

### HITL state controls

The gateway implements self-contained HMAC-signed state tokens with:

- issuer, issued-at, expiry, and JTI claims
- optional previous-key verification during rotation
- subject binding for generated approval tokens
- replay protection
- Redis/Memorystore-backed atomic JTI consumption for staging/production

In staging/production the replay store fails closed. An in-memory replay store is only allowed for demo/development.

### Regulated-workflow prototype

The repository contains demonstrations of controls often relevant to regulated workflows, including record hashing, signature meaning, timestamping, authentication, replay protection, and audit metadata.

These are labeled **Part 11-aligned technical control prototypes**. The lab signing APIs are disabled by default and, when enabled, derive signer identity from verified OIDC claims rather than caller-provided names.

They do **not** by themselves establish Part 11 compliance. A real validated system also requires, among other things, controlled access, authority checks, attributable identities, durable audit records, retention, procedures, training, validation evidence, change control, and operational governance.

### A2UI adapter

`a2ui_builder.py` is an internal omnichannel adapter that can generate Google Card v2, Slack Block Kit, Teams Adaptive Card, and web descriptors.

It is **not advertised as A2UI v1 production compliance**. As of this repository update, A2UI v0.9.1 is the current production release and v1.0 is a candidate. Treat the adapter schema (`adapter-1.0`) as project-specific.

## Repository layout

```text
option1_cloud_run_gateway/   HTTP/JSON policy gateway and A2A v1 interface
option2_grpc_service/        Local gRPC architecture experiment
option3_dual_plane/          Dual-plane architecture experiment / mocks
a2a_sdk/                     Project client/CLI helpers
portal/                      Interactive verification/demo portal
benchmarks/                  Local benchmark scripts and evidence artifacts
docs/                        Architecture/reference material
```

## Security defaults

The application intentionally fails closed.

- `APP_ENV` defaults to `demo`, not `development`.
- Mock authentication requires both `APP_ENV=development` and `ALLOW_DEV_AUTH=true`.
- Lab mutation/signing APIs require `ENABLE_LAB_ENDPOINTS=true` plus authentication.
- Staging/production require an injected strong `JWT_SECRET`.
- The historical signing secret once committed to this repository is permanently rejected.
- Staging/production approval consumption requires Redis/Memorystore.
- Cross-origin browser access is deny-by-default except exact configured origins.
- Production webhook callbacks are deny-by-default except exact configured hosts.
- Interactive API documentation is disabled in staging/production.

## Required production configuration

At minimum, review and explicitly set:

```bash
APP_ENV=production
JWT_SECRET=<managed high-entropy secret>
EXPECTED_AUDIENCE=<OIDC audience for this gateway>
REDIS_URL=<TLS-protected Redis/Memorystore endpoint>

# Optional, when proxying to an authenticated Google-hosted downstream agent
DOWNSTREAM_AGENT_URL=https://...
DOWNSTREAM_ID_TOKEN_AUDIENCE=https://...

# Exact comma-separated values; empty means no external callbacks/CORS.
WEBHOOK_ALLOWED_HOSTS=example.internal
CORS_ALLOWED_ORIGINS=https://admin.example.com

# Leave false unless this is an authenticated non-production lab.
ENABLE_LAB_ENDPOINTS=false
ALLOW_DEV_AUTH=false
TRUST_PROXY_HEADERS=false
```

Use a managed secret store and workload identity in the deployment platform. Do not commit secrets or long-lived downstream bearer tokens.

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

The public portal is a **demo/verification console**, not the production gateway control plane.

## Testing

```bash
pytest -q
python -m compileall option1_cloud_run_gateway option2_grpc_service option3_dual_plane portal a2a_sdk
```

CI runs syntax checks, unit/integration tests, dependency auditing, and lightweight repository policy checks.

## Benchmarks

Two benchmark classes are intentionally separated:

```bash
# In-process primitive timing only
python benchmarks/run_kpi_benchmarks.py

# Local loopback process/socket integration test
python benchmarks/live_real_load_test.py
```

Every generated benchmark artifact declares its environment and whether it is a production measurement.

Local timing is **not** a Cloud Run, Railway, network, concurrency, cold-scale, or production SLA measurement. Historical result files that mixed measurements and assumptions have been retired.

## Demo versus production

| Capability | Public/demo portal | Production expectation |
|---|---|---|
| Identity | clearly labeled simulated UI identity unless protected lab auth is used | verified enterprise IdP/OIDC |
| Task state | ephemeral demo registry | durable downstream A2A service |
| Replay ledger | in-memory allowed | Redis/Memorystore or equivalent atomic store |
| Signature UI | simulation unless authenticated lab API is enabled | validated attributable signing process |
| Audit evidence | demo metadata/in-memory examples | durable append-only/retained audit system |
| Benchmarks | local/stored evidence | environment-specific load tests |
| Compliance | mapping/prototype only | customer validation and governance |
| Cross-origin access | local development origins | exact allowlist only |

## Current limitations

The repository still contains architecture experiments and UI demonstrations that are intentionally not production services. In particular:

- the portal is a large monolithic demo frontend
- Option 2 and Option 3 include local simulation/mock components
- the public demo portal and a hardened production admin/control plane should be deployed as separate services
- durable regulatory evidence storage is not implemented in this repository's lab APIs
- no software repository can make a blanket compliance claim independent of deployment and operating controls

See `SECURITY.md`, `ARCHITECTURE.md`, and `RUNBOOK.md` for the current implementation contract.

## Historical design documents

Several longer strategy/presentation documents in this repository capture earlier design exploration. They are useful as proposals but may contain historical targets, examples, or assumptions. They are **not source-of-truth evidence** for current implementation, protocol compliance, security posture, performance, or regulatory validation.

The current source of truth is:

1. executable code
2. automated tests/CI
3. this README
4. `SECURITY.md`
5. `ARCHITECTURE.md`
6. `RUNBOOK.md`

## Responsible use

Do not place real patient data, credentials, regulated records, or production signing keys into the public demo portal.

For production use, perform threat modeling, privacy/security review, protocol conformance testing, load testing, disaster-recovery testing, validation planning, and independent approval by the relevant enterprise control owners.
