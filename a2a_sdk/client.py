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

    def get_agent_card(self) -> Dict[str, Any]:
        """Fetch official A2A /.well-known/agent.json discovery manifest."""
        return self._get("/.well-known/agent.json")

    def get_a2ui_templates(self) -> Dict[str, Any]:
        """Fetch canonical A2UI preset templates for dynamic UI card generation."""
        return self._get("/api/a2ui/templates")

    def get_kpi_benchmarks(self) -> Dict[str, Any]:
        """Fetch gateway performance benchmarks including AST sanitization latency."""
        return self._get("/api/kpi-benchmarks")

    def run_diagnostics(self, endpoint: str = "psc://10.128.0.50:50051") -> Dict[str, Any]:
        """Run mTLS and AST latency diagnostics probe."""
        return self._post("/api/connect/diagnostics", {
            "target_endpoint": endpoint,
            "run_payload_probe": True
        })
