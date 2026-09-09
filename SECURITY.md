# Security Policy & Regulatory Compliance: Enterprise A2A Gateway

## 1. Zero Clinical Cloud Egress Policy

The **Enterprise A2A Gateway** enforces strict data sovereignty for regulated biopharma enterprises. Under no circumstances may proprietary patient records, CDISC SDTM domains (Adverse Events `AE`, Laboratory Tests `LB`, Demographics `DM`), or raw clinical trial protocols be transmitted across unencrypted boundaries or utilized for public foundational model training.

### Core Safeguards:
1. **Zero Foundation Model Training**: All inference endpoints utilize zero-data-retention agreements on Google Cloud Vertex AI Sovereign Enclaves.
2. **Outside-In VPC Demarcation**: The internal clinical database is physically segregated from public networks using Google Cloud Private Service Connect (PSC) and VPC Service Controls.
3. **AST ADK Sanitization**: Prohibited internal orchestration keys (`__internal_trace__`, `adk_internal_context`) are stripped in memory in **under 28 µs** prior to payload egress.

---

## 2. FDA 21 CFR Part 11 Technical Controls & Alignment Scope

The gateway implements technical software controls aligned with FDA 21 CFR Part 11 and GAMP 5 principles for electronic records and electronic signatures. Note: As with all software platforms, formal 21 CFR Part 11 compliance is an organizational certification requiring customer-specific standard operating procedures (SOPs), user training, access governance, and installation/operational/performance qualification (IQ/OQ/PQ) in addition to technical controls:

| Regulation Section | Requirement | Gateway Technical Implementation |
| :--- | :--- | :--- |
| **21 CFR §11.10(a)** | System Validation & Reliability | Deterministic unit, security, and E2E test suites with automated schema validation and continuous integration gates. |
| **21 CFR §11.10(e)** | Computer-Generated Audit Trails | Durable SQLite WAL / Cloud Logging append-only ledger with cryptographic SHA-256 hash chaining for all registration and signature events. |
| **21 CFR §11.50** | Signature Manifestation | Sealed state cards explicitly render Signer Identity, Professional Role, Verification Timestamp (UTC ISO 8601), and Statutory Meaning taxonomy. |
| **21 CFR §11.70** | Signature Linking | Cryptographic HMAC-SHA256 signature tightly binds the document digest, clinical payload parameters, and signer identity, rendering any post-signature mutation detectable. |

---

## 3. Cryptographic Token Tamper Guard & Key Management

### Stateless 48-Hour TTL State Tokens
All Human-in-the-Loop (HITL) approval actions are protected by cryptographic HMAC-SHA256 tokens:
- **Algorithm**: `HMAC-SHA256` using constant-time string comparison (`hmac.compare_digest`) to prevent timing side-channel attacks.
- **TTL**: Hard expiration enforced after 48 hours (172,800 seconds).
- **Tamper Rejection**: Any alteration of clinical parameters (e.g. mutating dosage from `300mg` to `400mg` in transit) invalidates the signature and raises an **HTTP 401 Unauthorized** security alert.
- **Fail-Closed Anti-Replay Store**: Unique JWT IDs (`jti`) are tracked in `RedisJTIStore`. In `APP_ENV=production`, if Redis is unreachable, the gateway fails closed (`HTTP 503 Service Unavailable`) rather than falling back to uncoordinated local memory, preventing distributed cross-replica replay attacks.

### Dual-Key Rotation Procedure:
1. **Zero-Downtime Rollover**: Secrets are managed via `GATEWAY_HMAC_SECRET` (Primary) and `GATEWAY_HMAC_SECRET_SECONDARY` (Secondary).
2. **Rotation Lifecycle**:
   - **Step 1**: Provision the candidate secret in Secret Manager and configure it as `GATEWAY_HMAC_SECRET_SECONDARY`.
   - **Step 2**: Promote the candidate secret to `GATEWAY_HMAC_SECRET` and set the former primary as `GATEWAY_HMAC_SECRET_SECONDARY`. New tokens are signed with the primary key; existing in-flight tokens signed under the prior key remain verifiable throughout their 48-hour TTL window.
   - **Step 3**: Once in-flight tokens expire (48 hours), remove `GATEWAY_HMAC_SECRET_SECONDARY`.

---

## 4. AST Sanitizer & Confused Deputy Defenses

1. **Sub-28 µs In-Memory Sanitization**: Outbound payloads are filtered via recursive AST dictionary traversal (`sanitize_payload_ast()`) to strip internal envelopes (`__internal_trace__`, `adk_internal_context`, `system_override`, `leaked_jwt_secret`, `prompt_injection_flags`) and prefixes (`__adk`, `__internal`, `_adk`, `x_adk`, `ge_`).
2. **Credential Stripping**: Sensitive ingress authorization headers (`Authorization`, `Proxy-Authorization`) are stripped prior to downstream task dispatch, eliminating confused-deputy credential forwarding.
3. **SSE Stream Protection**: Server-Sent Event (SSE) streams are sanitized on a per-line basis (`sanitize_sse_line`) to eliminate partial JSON buffer token leaks. Non-JSON payloads are blocked.
4. **Rate-Limiter Spoof Defense**: Sliding-window rate limiters inspect the rightmost ingress hop in `X-Forwarded-For` to prevent client spoofing of proxy chains.

---

## 5. Reporting Security Vulnerabilities

We take the security of clinical systems seriously. If you discover a security vulnerability or potential data leakage vector within the Enterprise A2A Gateway, please report it immediately:

- **Security Team Contact**: `security@biopharma-a2a-gateway.internal`
- **Response Window**: Initial acknowledgment within 24 hours; remediation assessment within 72 hours.
- **Coordinated Disclosure**: Please refrain from publicly disclosing the issue until a patch has been validated and released.
