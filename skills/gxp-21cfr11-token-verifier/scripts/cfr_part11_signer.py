#!/usr/bin/env python3
"""
FDA 21 CFR Part 11 Stateless HMAC-SHA256 Electronic Signature Signer & Verifier.

Reference implementation for sovereign biopharma agent swarms communicating
with the Enterprise A2A Gateway at https://a2a-gateway-638420508320.us-central1.run.app.
"""

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


class CFRPart11Signer:
    """Stateless cryptographic signer satisfying 21 CFR Part 11 rules:
    - § 11.50 (Manifestation of Signatures: printed name, timestamp, meaning)
    - § 11.70 (Signature/Record Linking: SHA-256 digest of clinical payload)
    - § 11.200 / 11.300 (Credentials: Double-envelope HMAC key authentication)
    """

    SUPPORTED_MEANINGS = [
        "ProtocolApproval",
        "CohortValidation",
        "SafetyReview",
        "SystemAudit",
        "DoseTitrationApproval",
        "DeviationJustification",
    ]

    def __init__(self, hmac_secret_key: bytes):
        if not isinstance(hmac_secret_key, bytes):
            if isinstance(hmac_secret_key, str):
                hmac_secret_key = hmac_secret_key.encode("utf-8")
            else:
                raise TypeError("hmac_secret_key must be bytes or str")
        self.secret_key = hmac_secret_key

    def create_signature_payload(
        self,
        agent_id: str,
        agent_name: str,
        meaning: str,
        document_id: str,
        document_data: bytes,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates a 21 CFR Part 11 compliant metadata payload and signs it."""
        if isinstance(document_data, str):
            document_data = document_data.encode("utf-8")
        elif not isinstance(document_data, bytes):
            document_data = json.dumps(document_data, sort_keys=True).encode("utf-8")

        # Create SHA-256 hash of clinical data / document (§ 11.70 record linking)
        document_hash = hashlib.sha256(document_data).hexdigest()

        payload = {
            "signer_id": agent_id,
            "signer_name": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meaning": meaning,
            "document_id": document_id,
            "document_hash": document_hash,
        }
        if extra_metadata:
            payload["extra_metadata"] = extra_metadata

        # Serialize payload deterministically (alphabetically sorted keys)
        serialized_payload = json.dumps(payload, sort_keys=True).encode("utf-8")

        # Generate stateless HMAC-SHA256 signature
        signature = hmac.new(self.secret_key, serialized_payload, hashlib.sha256).hexdigest()

        return {
            "payload": payload,
            "signature": signature,
        }

    def verify_signature(self, signed_envelope: Dict[str, Any]) -> Tuple[bool, str]:
        """Statelessly verifies the signature integrity of the incoming package.
        Returns (is_valid, reason).
        """
        payload = signed_envelope.get("payload")
        provided_signature = signed_envelope.get("signature")

        if not payload or not provided_signature:
            return False, "Missing payload or signature in envelope"

        # Validate mandatory 21 CFR Part 11 § 11.50 fields
        required_fields = ["signer_id", "signer_name", "timestamp", "meaning", "document_id", "document_hash"]
        for field in required_fields:
            if field not in payload:
                return False, f"Non-compliant envelope: missing § 11.50 attribute '{field}'"

        serialized_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
        expected_signature = hmac.new(self.secret_key, serialized_payload, hashlib.sha256).hexdigest()

        # Constant-time comparison to prevent timing side-channel attacks
        is_valid = hmac.compare_digest(expected_signature, provided_signature)
        if not is_valid:
            return False, "Cryptographic signature mismatch: record altered in transit"

        return True, "21 CFR Part 11 Signature verified statelessly"


if __name__ == "__main__":
    SECRET_KEY = b"secure-swarm-gateway-handshake-key-991"
    signer = CFRPart11Signer(SECRET_KEY)

    protocol_document = b"CLINICAL TRIAL PROTOCOL: Phase IIa sovereign mRNA target mapping..."

    signed_package = signer.create_signature_payload(
        agent_id="agent_cohort_matcher_04",
        agent_name="Autonomous Cohort Matching Agent (v2.1)",
        meaning="CohortValidation",
        document_id="protocol_amendment_v3.2",
        document_data=protocol_document,
    )

    print("--- GENERATED COMPLIANT SIGNATURE PACKAGE ---")
    print(json.dumps(signed_package, indent=2))

    is_valid, reason = signer.verify_signature(signed_package)
    print(f"\nSignature Authenticated statelessly? -> {is_valid} ({reason})")
    assert is_valid is True
