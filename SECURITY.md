# Security Policy & Regulatory Compliance: Enterprise A2A Gateway

## 1. Zero Clinical Cloud Egress Policy

The **Enterprise A2A Gateway** enforces strict data sovereignty for regulated biopharma enterprises. Under no circumstances may proprietary patient records, CDISC SDTM domains (Adverse Events `AE`, Laboratory Tests `LB`, Demographics `DM`), or raw clinical trial protocols be transmitted across unencrypted boundaries or utilized for public foundational model training.

### Core Safeguards:
1. **Zero Foundation Model Training**: All inference endpoints utilize zero-data-retention agreements on Google Cloud Vertex AI Sovereign Enclaves.
2. **Outside-In VPC Demarcation**: The internal clinical database is physically segregated from public networks using Google Cloud Private Service Connect (PSC) and VPC Service Controls.
3. **AST ADK Sanitization**: Prohibited internal orchestration keys (`__internal_trace__`, `adk_internal_context`) are stripped in memory in **under 28 µs** prior to payload egress.

---

## 2. FDA 21 CFR Part 11 Regulatory Compliance

The gateway provides native compliance mechanisms for electronic records and electronic signatures in accordance with FDA 21 CFR Part 11 and GAMP 5 guidance:

| Regulation Section | Requirement | Gateway Technical Implementation |
| :--- | :--- | :--- |
| **21 CFR §11.10(a)** | System Validation & Reliability | Deterministic unit and E2E test suites running on Google signed Chrome with full audit logging. |
| **21 CFR §11.10(e)** | Computer-Generated Audit Trails | Immutable Cloud Logging events recording signer identity, timestamp, and signature digests. |
| **21 CFR §11.50** | Signature Manifestation | Sealed state cards explicitly display Signer Full Name, Professional Role, Date/Time, and Meaning. |
| **21 CFR §11.70** | Signature Linking | Cryptographic HMAC-SHA256 signature binds the exact dosing payload parameters directly to the signature hash. |

---

## 3. Cryptographic Token Tamper Guard

### Stateless 48-Hour TTL State Tokens
All Human-in-the-Loop (HITL) approval actions are protected by cryptographic HMAC-SHA256 tokens:
- **Algorithm**: `HMAC-SHA256` using constant-time string comparison (`hmac.compare_digest`).
- **TTL**: Hard expiration enforced after 48 hours ($172,800$ seconds).
- **Tamper Rejection**: Any alteration of clinical parameters (e.g. mutating dosage from `300mg` to `400mg` in transit) invalidates the signature and raises an **HTTP 401 Unauthorized** security alert.

### Key Rotation Procedure:
1. Secret keys are injected exclusively via environment variables (`GATEWAY_HMAC_SECRET`) or Google Cloud Secret Manager.
2. The verification engine supports dual-key rotation windows to validate in-flight tokens during key rollover.

---

## 4. Reporting Security Vulnerabilities

We take the security of clinical systems seriously. If you discover a security vulnerability or potential data leakage vector within the Enterprise A2A Gateway, please report it immediately:

- **Security Team Contact**: `security@biopharma-a2a-gateway.internal`
- **Response Window**: Initial acknowledgment within 24 hours; remediation assessment within 72 hours.
- **Coordinated Disclosure**: Please refrain from publicly disclosing the issue until a patch has been validated and released.
