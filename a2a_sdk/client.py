"""
Enterprise A2A Gateway Python Client SDK.

Provides typed interfaces for:
- 1-Click FDA eCTD 3.2.2 Automated Regulatory Dossier Compilation
- In-Silico 10,000 Digital Twin Patient Trial Simulation
- Sub-28µs In-Memory AST Orchestration Sanitization
- Stateless 21 CFR Part 11 HMAC-SHA256 Signatures
- PromptCanvas Draw.io Architecture ⟷ A2A DAG Compilation
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

class A2AGatewayClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8090"):
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "A2A-Gateway-Python-SDK/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"HTTP {e.code} Error from A2A Gateway: {err_body}")

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "A2A-Gateway-Python-SDK/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"HTTP {e.code} Error from A2A Gateway: {err_body}")

    def health(self) -> Dict[str, Any]:
        """Check status across Option 1, Option 2, and Option 3 gateways."""
        return self._get("/api/health/all")

    def compile_ectd(
        self,
        protocol_id: str = "MK-3475-087",
        amendment_id: str = "AMD-ONC-2026-08",
        target_dose_mg: float = 250.0,
        sponsor_name: str = "Merck Sharp & Dohme LLC"
    ) -> Dict[str, Any]:
        """Compile complete FDA Form 1571/1572, Merkle signature ledger, and eCTD XML bundle in < 25ms."""
        return self._post("/api/ectd/compile", {
            "protocol_id": protocol_id,
            "amendment_id": amendment_id,
            "target_dose_mg": target_dose_mg,
            "sponsor_name": sponsor_name
        })

    def simulate_in_silico(
        self,
        cohort_size: int = 10000,
        dose_mg: float = 250.0,
        biomarker_cutoff_percent: float = 50.0,
        prophylactic_protectant: bool = True
    ) -> Dict[str, Any]:
        """Execute 10,000 synthetic patient PK/PD trial simulation across 24 weeks."""
        return self._post("/api/insilico/simulate", {
            "cohort_size": cohort_size,
            "dose_mg": dose_mg,
            "biomarker_cutoff_percent": biomarker_cutoff_percent,
            "prophylactic_protectant": prophylactic_protectant
        })

    def compile_promptcanvas_diagram(self, drawio_xml: str) -> Dict[str, Any]:
        """Compile PromptCanvas Draw.io mxGraphModel XML into an executable A2A Gateway DAG."""
        return self._post("/api/promptcanvas/compile-to-dag", {
            "drawio_xml": drawio_xml,
            "target_protocol": "a2a.v1.0.0",
            "enforce_ast_sanitization": True
        })

    def export_drawio_preset(self, preset_key: str = "option3_dual_plane") -> Dict[str, Any]:
        """Export preset architecture directly to Draw.io XML."""
        return self._post("/api/promptcanvas/export-xml", {
            "architecture_preset": preset_key
        })

    def run_diagnostics(self, endpoint: str = "psc://10.128.0.50:50051") -> Dict[str, Any]:
        """Run mTLS and AST latency diagnostics probe."""
        return self._post("/api/connect/diagnostics", {
            "target_endpoint": endpoint,
            "run_payload_probe": True
        })
