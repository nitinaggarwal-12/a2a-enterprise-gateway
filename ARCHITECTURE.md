# Current Architecture

This document describes the current repository implementation after the enterprise-hardening pass.

> The architecture experiments in Option 2/Option 3 and the public portal are not equivalent to a validated production control plane.

## 1. Runtime surfaces

### Production-oriented gateway

`option1_cloud_run_gateway.app.main:app`

Responsibilities:

1. verify caller OIDC identity
2. expose the standards-facing A2A v1 JSON-RPC interface
3. normalize/sanitize payloads and transport headers
4. prevent caller credential forwarding
5. mint optional destination-specific downstream identity
6. enforce callback/SSRF rules
7. generate subject-bound HITL state
8. atomically consume approval JTIs
9. sanitize supported downstream response formats

### Demo/verification portal

`portal.app:app`

Responsibilities:

- interactive product demonstration
- local architecture experiments
- stored benchmark visualization
- A2UI adapter examples
- explicitly gated lab APIs

The portal is not the recommended public production gateway/control-plane deployment. Separate it from production gateway/admin services for real enterprise deployments.

## 2. A2A v1 interface

```text
GET  /.well-known/agent-card.json
POST /a2a/v1
A2A-Version: 1.0
```

The Agent Card publishes a JSON-RPC binding and only advertises implemented capabilities.

Current demo implementation:

- SendMessage
- GetTask
- ListTasks
- CancelTask

Not advertised:

- streaming on the v1 surface
- push notifications on the v1 surface
- extended Agent Card

Unsupported calls return explicit A2A errors.

The older `/.well-known/agent.json` path is a deprecation redirect.

## 3. Request trust pipeline

```text
Untrusted caller
   |
   v
[OIDC audience verification]
   |
   v
[A2A/JSON-RPC structural validation]
   |
   v
[policy sanitizer]
   |- known orchestration metadata removed
   |- credential-bearing fields removed
   |- top-level envelope allowlisted
   |- caller auth/cookies/proxy headers removed
   |
   v
[tenant/data policy -- deployment responsibility]
   |
   v
[destination-specific ADC ID token, optional]
   |
   v
[downstream A2A agent]
```

The sanitizer is one layer. A production data-governance architecture should add explicit schemas, tenant authorization, DLP/classification, tool policy, and output policy.

## 4. Response policy

JSON downstream responses are sanitized before returning.

For the legacy SSE proxy path, the gateway buffers complete SSE events and requires JSON `data:` frames. Each JSON frame is sanitized. Opaque data frames are rejected.

Opaque non-JSON responses on the policy proxy are rejected rather than passed through unsanitized.

## 5. Human approval controls

```text
Task requires review
   |
   v
state token
  - task context
  - decision
  - approver subject
  - iss / iat / exp / jti
   |
   v
user authenticates
   |
   v
subject equality check
   |
   v
atomic JTI consume
   |
   +--> first execution: accepted
   |
   +--> replay: 409
```

Demo/development can use an in-process JTI ledger.

Staging/production require a distributed atomic Redis/Memorystore ledger and fail closed when it is missing/unavailable.

## 6. Key rotation

- `JWT_SECRET`: current signing key
- `JWT_PREVIOUS_SECRET`: optional verify-only previous key

New tokens use the current key. Verification can temporarily accept the previous key during controlled rotation.

The published historical default secret is rejected.

For higher assurance, migrate the signing primitive to KMS/HSM.

## 7. Webhook/egress boundary

Production callback policy requires:

- HTTPS
- exact hostname in `WEBHOOK_ALLOWED_HOSTS`
- public routable address
- no link-local/cloud metadata/private/special-use target

This application check should be paired with network-level egress controls.

## 8. Browser boundary

Cross-origin access:

- local demo/development origins are explicitly listed
- production origins come only from `CORS_ALLOWED_ORIGINS`
- no wildcard Railway/Cloud Run origin rule

Baseline security headers are applied. Interactive OpenAPI/Swagger docs are disabled outside demo/development on the production-oriented gateway.

## 9. Regulated-control model

The code demonstrates technical building blocks such as:

- identity
- record hash linkage
- signature meaning
- timestamp
- replay prevention
- audit metadata

These are not sufficient for a blanket Part 11/GxP claim.

The protected lab signing APIs:

- are disabled by default
- require OIDC authentication
- derive signer ID/name from auth claims
- require canonical document content for record-link verification

Their resource registries remain in-memory demos and therefore are not a regulated system of record.

## 10. Option 2 / Option 3

`option2_grpc_service/` and `option3_dual_plane/` are architecture experiments. Benchmarking them locally can inform design choices, but local timing must not be represented as production performance.

Before adopting either as a production plane, require:

- production identity model
- durable state
- deployment manifests/IaC
- health/readiness
- telemetry
- security policy parity
- load/failure tests
- protocol conformance tests
- operational runbook
- rollback/DR plan

## 11. Recommended target decomposition

For enterprise production, split the current combined experience into independently deployed surfaces:

```text
A2A Data Plane Gateway
  - protocol
  - identity
  - policy
  - routing
  - telemetry

Admin / Trust Control Plane
  - agent registry
  - policy configuration
  - transaction traces
  - evidence
  - operational health

Demo / Labs
  - A2UI examples
  - architecture experiments
  - simulations
  - benchmark viewers
```

This reduces attack surface and prevents a demo feature from inheriting production authority.

## 12. Evidence hierarchy

Do not infer implementation from screenshots or strategy slides.

Use this order:

1. code at the deployed commit
2. CI results
3. environment-specific test evidence
4. README / SECURITY / this document / RUNBOOK
5. historical design documents and screenshots
