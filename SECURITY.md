# Security Model

## Status

This project implements security controls for an A2A gateway and a separate demo portal. It is a reference implementation, not a certification or compliance attestation.

The production security posture depends on deployment configuration, identity infrastructure, network controls, data classification, key management, monitoring, operational procedures, and validation evidence.

## Trust boundaries

The intended production flow is:

```text
Caller
  -> verified gateway OIDC audience
  -> protocol/schema/policy sanitization
  -> destination-specific downstream identity
  -> downstream A2A agent
```

The caller's bearer token is never forwarded to the downstream service.

If `DOWNSTREAM_ID_TOKEN_AUDIENCE` is configured, the gateway mints a new Google ID token from Application Default Credentials for that exact destination audience.

## Authentication

Mock auth is disabled by default.

It can only be enabled when:

```text
APP_ENV=development
ALLOW_DEV_AUTH=true
```

Demo, staging, and production otherwise require a Google OIDC bearer token validated against `EXPECTED_AUDIENCE`.

The lab registration/signing APIs also require `ENABLE_LAB_ENDPOINTS=true`. Enabling lab mode does not bypass authentication.

## Signing keys and HITL state

`JWT_SECRET` signs HITL state tokens.

Requirements:

- staging/production must inject a strong secret
- the repository's historical published default is explicitly rejected
- `JWT_PREVIOUS_SECRET` may be configured temporarily for verification during key rotation
- new tokens are signed only with the current key
- tokens require `iss`, `iat`, `exp`, and `jti`
- generated approval tokens can be bound to the authenticated subject

For higher-assurance deployments, move signing operations to Cloud KMS/HSM or another approved key-management boundary rather than relying on an application-held symmetric secret.

## Replay protection

Approval execution uses atomic JTI consumption.

- demo/development may use the in-memory store
- staging/production require `REDIS_URL` or `MEMORYSTORE_URL`
- Redis failures fail closed in staging/production
- no silent local-memory downgrade is permitted in staging/production

This means approval tokens are self-contained for context but the system is not literally stateless: replay safety depends on a durable nonce ledger.

## Webhook and SSRF controls

Outbound callback URLs are validated for:

- HTTP/HTTPS scheme
- HTTPS in staging/production
- cloud metadata destinations
- link-local, loopback, private, multicast, reserved, and unspecified addresses
- exact production hostname allowlisting through `WEBHOOK_ALLOWED_HOSTS`

An empty production webhook allowlist denies external callbacks.

DNS validation reduces SSRF risk but does not replace a network-level egress policy. Production deployments should also constrain egress using platform/network controls.

## Payload and header policy

The sanitizer removes known internal orchestration keys and obvious credential-bearing fields. The policy gateway also:

- allowlists top-level A2A/JSON-RPC envelope fields
- removes caller authorization/cookie/API-key headers
- removes proxy/hop-by-hop headers
- sanitizes JSON SSE data frames
- rejects opaque non-JSON SSE data
- rejects non-JSON downstream responses on the sanitizing proxy path

This is a finite defense-in-depth policy and must not be described as a universal "zero leak" guarantee.

For sensitive deployments add explicit schemas, data classification/DLP, tenant policy, tool authorization, and output policy.

## CORS and browser surface

Cross-origin access is deny-by-default outside local development.

Use `CORS_ALLOWED_ORIGINS` for exact trusted origins. The gateway does not use a wildcard `*.run.app` credentialed CORS rule.

Baseline response headers include content-type sniffing protection, referrer policy, frame restrictions, and permissions policy. HSTS is added in staging/production.

## Part 11 / regulated workflows

The repository demonstrates technical controls that may contribute to a validated regulated system, including:

- verified user identity
- signature meaning
- record hash linking
- timestamps
- replay prevention
- audit metadata

These controls are intentionally labeled **Part 11-aligned technical control prototypes**.

The repository does not claim that an application deployment is FDA 21 CFR Part 11 compliant. Compliance/validation also requires controls outside these helper functions, including access authorization, durable audit trails, retention, procedures, training, validation, change control, record availability, and organizational governance.

The public portal's ordinary A2UI action endpoint creates a **demo approval marker**, not an attributable electronic signature. Protected lab signing derives signer identity from OIDC and is disabled by default.

## Persistence

The lab's swarm/signature registries are in-memory demonstrations and therefore are not suitable as regulated system-of-record storage.

Do not enable those APIs as a production record system. A production design needs durable, retained, tamper-evident/append-only evidence storage with backup, recovery, and inspection procedures.

## Secrets

Never commit:

- `JWT_SECRET`
- `JWT_PREVIOUS_SECRET`
- Redis credentials
- service-account keys
- API keys
- production bearer tokens
- signing private keys

Use the deployment platform's managed secret mechanism and workload identity.

## Reporting vulnerabilities

For a public repository, use GitHub's private vulnerability reporting/security advisory mechanism when available. Do not publish secrets, patient information, or exploit details in a public issue.
