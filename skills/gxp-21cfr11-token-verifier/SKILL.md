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

### Step 2: Validation Scenarios Covered
1. **Valid Token Flow**: Signs a MK-3475 dose titration record and verifies matching HMAC digest.
2. **Expired Token Flow**: Verifies rejection of tokens exceeding 48-hour TTL ($> 172,800$s).
3. **Byte-Level Payload Tampering**: Simulates mutating dose `300mg` to `400mg` in transit, confirming HTTP 401 Unauthorized rejection via `hmac.compare_digest()`.
4. **Secret Key Rotation**: Verifies tokens signed with previous secret keys are rejected unless dual-key transition window is active.
