"""Durable Regulatory Audit & ROA Registry Ledger.

Implements 21 CFR § 11.10(e) computer-generated, time-stamped audit trails
with SQLite ACID storage and cryptographic hash chaining for regulatory record integrity.
"""

import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Storage location in repository workspace or data directory
DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "audit_ledger.db"


class DurableAuditLedger:
    """Thread-safe SQLite persistent store for swarms, registrations, signatures, and audit trails."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._lock = threading.RLock()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_database(self):
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS swarms (
                            client_id TEXT PRIMARY KEY,
                            client_name TEXT NOT NULL,
                            organization TEXT NOT NULL,
                            record_json TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        );
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS registrations (
                            registration_id TEXT PRIMARY KEY,
                            client_id TEXT NOT NULL,
                            record_json TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        );
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS signatures (
                            receipt_id TEXT PRIMARY KEY,
                            signer_id TEXT NOT NULL,
                            signer_name TEXT NOT NULL,
                            meaning TEXT NOT NULL,
                            document_id TEXT NOT NULL,
                            document_hash TEXT NOT NULL,
                            record_json TEXT NOT NULL,
                            verified_at TEXT NOT NULL
                        );
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS dossiers (
                            dossier_id TEXT PRIMARY KEY,
                            record_json TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        );
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS audit_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            event_type TEXT NOT NULL,
                            actor_id TEXT NOT NULL,
                            action TEXT NOT NULL,
                            details_json TEXT NOT NULL,
                            prev_hash TEXT NOT NULL,
                            event_hash TEXT NOT NULL,
                            timestamp TEXT NOT NULL
                        );
                    """)

                # Seed standard verified records if table is empty
                self._seed_default_records(conn)
            finally:
                conn.close()

    def _seed_default_records(self, conn: sqlite3.Connection):
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM swarms;")
        if cur.fetchone()[0] == 0:
            now_iso = datetime.now(timezone.utc).isoformat()
            # Seed verified demo swarm
            default_swarm_id = "swarm-oncology-01"
            default_reg_id = "reg-21cfr11-default"
            swarm_record = {
                "status": "REGISTERED",
                "client_id": default_swarm_id,
                "client_name": "Dr. Sarah Chen Swarm",
                "organization": "Sovereign Therapeutics Corp",
                "registration_id": default_reg_id,
                "registered_at": now_iso,
                "gateway_target": "https://a2a-gateway-638420508320.us-central1.run.app",
                "security_scheme": "HMAC-SHA256",
                "compliance_status": "21_CFR_PART_11_ALIGNED",
                "supported_meanings": [
                    "ProtocolApproval",
                    "CohortValidation",
                    "SafetyReview",
                    "SystemAudit",
                    "DoseTitrationApproval",
                    "DeviationJustification",
                ],
                "verification_endpoint": "/api/v1/verify-signature",
                "uri": f"/api/v1/swarms/{default_swarm_id}",
                "_links": {
                    "self": {"href": f"/api/v1/swarms/{default_swarm_id}"},
                    "registration": {"href": f"/api/v1/registrations/{default_reg_id}"},
                    "verify": {"href": "/api/v1/verify-signature"},
                },
                "message": "Default verified sovereign biopharma agent swarm.",
            }
            with conn:
                conn.execute(
                    "INSERT INTO swarms (client_id, client_name, organization, record_json, created_at) VALUES (?, ?, ?, ?, ?);",
                    (default_swarm_id, swarm_record["client_name"], swarm_record["organization"], json.dumps(swarm_record), now_iso),
                )
                conn.execute(
                    "INSERT INTO registrations (registration_id, client_id, record_json, created_at) VALUES (?, ?, ?, ?);",
                    (default_reg_id, default_swarm_id, json.dumps(swarm_record), now_iso),
                )

        cur.execute("SELECT COUNT(*) FROM dossiers;")
        if cur.fetchone()[0] == 0:
            now_iso = datetime.now(timezone.utc).isoformat()
            # Seed standard FDA inspection dossier
            default_dossier_id = "FDA-AUDIT-2026-A2A-09881"
            dossier_record = {
                "dossier_id": default_dossier_id,
                "inspection_id": "FDA-AUDIT-2026-A2A-09881",
                "status": "CONFORMANT_READY_FOR_BLA",
                "compliance": "21_CFR_PART_11_ALIGNED",
                "study_id": "MK-3475-087",
                "created_at": now_iso,
                "uri": f"/api/v1/dossiers/{default_dossier_id}",
                "_links": {
                    "self": {"href": f"/api/v1/dossiers/{default_dossier_id}"},
                    "inspection": {"href": "/api/google-labs/fda-inspection-dossier"},
                },
            }
            with conn:
                conn.execute(
                    "INSERT INTO dossiers (dossier_id, record_json, created_at) VALUES (?, ?, ?);",
                    (default_dossier_id, json.dumps(dossier_record), now_iso),
                )

    def save_dossier(self, dossier_id: str, record: Dict[str, Any]):
        with self._lock:
            conn = self._get_connection()
            try:
                now_iso = datetime.now(timezone.utc).isoformat()
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO dossiers (dossier_id, record_json, created_at) VALUES (?, ?, ?);",
                        (dossier_id, json.dumps(record), now_iso),
                    )
            finally:
                conn.close()

    def save_swarm(self, client_id: str, registration_id: str, record: Dict[str, Any]):
        with self._lock:
            conn = self._get_connection()
            try:
                now_iso = datetime.now(timezone.utc).isoformat()
                record_str = json.dumps(record)
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO swarms (client_id, client_name, organization, record_json, created_at) VALUES (?, ?, ?, ?, ?);",
                        (client_id, record.get("client_name", ""), record.get("organization", ""), record_str, now_iso),
                    )
                    conn.execute(
                        "INSERT OR REPLACE INTO registrations (registration_id, client_id, record_json, created_at) VALUES (?, ?, ?, ?);",
                        (registration_id, client_id, record_str, now_iso),
                    )
                self.append_audit_event(
                    event_type="SWARM_REGISTRATION",
                    actor_id=client_id,
                    action="REGISTER",
                    details={"registration_id": registration_id, "organization": record.get("organization")},
                )
            finally:
                conn.close()

    def get_swarm(self, client_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT record_json FROM swarms WHERE client_id = ?;", (client_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            conn.close()

    def get_registration(self, registration_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT record_json FROM registrations WHERE registration_id = ?;", (registration_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            conn.close()

    def save_signature_receipt(self, receipt_id: str, receipt: Dict[str, Any]):
        with self._lock:
            conn = self._get_connection()
            try:
                now_iso = datetime.now(timezone.utc).isoformat()
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO signatures (receipt_id, signer_id, signer_name, meaning, document_id, document_hash, record_json, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                        (
                            receipt_id,
                            receipt.get("signer_id", ""),
                            receipt.get("signer_name", ""),
                            receipt.get("meaning", ""),
                            receipt.get("document_id", ""),
                            receipt.get("document_hash", ""),
                            json.dumps(receipt),
                            now_iso,
                        ),
                    )
                self.append_audit_event(
                    event_type="SIGNATURE_VERIFICATION",
                    actor_id=receipt.get("signer_id", "anonymous"),
                    action="VERIFY",
                    details={"receipt_id": receipt_id, "document_id": receipt.get("document_id"), "meaning": receipt.get("meaning")},
                )
            finally:
                conn.close()

    def get_signature_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT record_json FROM signatures WHERE receipt_id = ?;", (receipt_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            conn.close()

    def get_dossier(self, dossier_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT record_json FROM dossiers WHERE dossier_id = ?;", (dossier_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            conn.close()

    def append_audit_event(
        self,
        event_type: str,
        actor_id: str,
        action: str,
        details: Dict[str, Any],
    ) -> str:
        """Append an immutable 21 CFR § 11.10(e) audit trail event with cryptographic hash chaining."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("BEGIN IMMEDIATE;")
                cur = conn.cursor()
                cur.execute("SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1;")
                row = cur.fetchone()
                prev_hash = row[0] if row else "GENESIS_BLOCK_A2A_GATEWAY_2026"

                now_iso = datetime.now(timezone.utc).isoformat()
                details_str = json.dumps(details, sort_keys=True)
                to_hash = f"{prev_hash}|{event_type}|{actor_id}|{action}|{details_str}|{now_iso}"
                event_hash = hashlib.sha256(to_hash.encode("utf-8")).hexdigest()

                cur.execute(
                    "INSERT INTO audit_events (event_type, actor_id, action, details_json, prev_hash, event_hash, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?);",
                    (event_type, actor_id, action, details_str, prev_hash, event_hash, now_iso),
                )
                conn.commit()
                return event_hash
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def get_recent_audit_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, event_type, actor_id, action, details_json, prev_hash, event_hash, timestamp FROM audit_events ORDER BY id DESC LIMIT ?;",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r["id"],
                    "event_type": r["event_type"],
                    "actor_id": r["actor_id"],
                    "action": r["action"],
                    "details": json.loads(r["details_json"]),
                    "prev_hash": r["prev_hash"],
                    "event_hash": r["event_hash"],
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]
        finally:
            conn.close()


GLOBAL_LEDGER = DurableAuditLedger()
