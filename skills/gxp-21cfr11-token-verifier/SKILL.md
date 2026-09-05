---
name: gxp-21cfr11-token-verifier
description: >-
  Use this skill whenever verifying, testing, or auditing FDA 21 CFR Part 11
  compliant electronic signatures, HMAC-SHA256 signed state tokens, or simulating
  tamper security attacks in the Enterprise A2A Gateway.
---

# 21 CFR Part 11 Electronic Signature & State Token Verifier

This skill provides regulatory auditing and automated cryptographic validation for Human-in-the-Loop (HITL) dose titration workflows in the Enterprise A2A Gateway.

## Regulatory Framework
- **FDA 21 CFR §11.50**: Requires signatures to contain printed name of signer, date/time executed, and meaning (approval/review).
- **FDA 21 CFR §11.70**: Signatures must be linked to their respective electronic records to ensure signatures cannot be excised, copied, or transferred.
- **HMAC-SHA256 Stateless Architecture**: 48-hour TTL state tokens avoid relational database write-lock contention.

## Execution Steps

### Step 1: Run Cryptographic Signature & Tamper Suite
Execute the token validation script:

```bash
.venv/bin/python skills/gxp-21cfr11-token-verifier/scripts/verify_tokens.py
```

### Step 2: Run Sovereign Swarm CFRPart11Signer Micro-Utility
Execute the swarm signer and verifier ceremony:

```bash
.venv/bin/python skills/gxp-21cfr11-token-verifier/scripts/cfr_part11_signer.py
```

### Step 3: Gateway Swarm Endpoints
- **Swarm Registration**: `POST /api/v1/register`
- **Stateless Signature Verification**: `POST /api/v1/verify-signature`
- **Live Gateway Target**: `https://a2a-gateway-638420508320.us-central1.run.app`

### Step 4: Validation Scenarios Covered
1. **Valid Token Flow**: Signs a MK-3475 dose titration record and verifies matching HMAC digest.
2. **Sovereign Swarm Envelope**: Verifies `CFRPart11Signer` envelope containing `document_hash`, `signer_id`, `meaning`, and `timestamp`.
3. **Expired Token Flow**: Verifies rejection of tokens exceeding 48-hour TTL ($> 172,800$s).
4. **Byte-Level Payload Tampering**: Simulates mutating payload in transit, confirming HTTP 401 Unauthorized rejection via `hmac.compare_digest()`.
5. **Secret Key Rotation**: Verifies tokens signed with previous secret keys are rejected unless dual-key transition window is active.

