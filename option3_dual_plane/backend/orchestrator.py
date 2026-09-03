"""Core Clinical Agent Platform Orchestrator (Plane 1).

Executes heavy multi-step clinical analysis workloads directly against Vertex AI,
completely isolated from Gemini Enterprise ADK containers and envelope injections.
Once background reasoning completes, passes the result to Plane 2 for HITL approval.
"""

import asyncio
import logging
from typing import Any, Dict
import httpx

from .config import config
from .vertex_client import VertexAIClinicalEngine, ClinicalAnalysisResult

logger = logging.getLogger("orchestrator")


class EnterpriseClinicalOrchestrator:
    """Orchestrator for Plane 1 Clinical Workloads."""

    def __init__(self):
        self.engine = VertexAIClinicalEngine()
        self.bridge_url = config.BRIDGE_SERVICE_URL

    async def run_study_safety_workflow(
        self,
        study_id: str = "MK-3475-087",
        cohort: str = "Cohort-B",
    ) -> Dict[str, Any]:
        """Execute full Plane 1 execution -> Plane 2 dispatch pipeline."""
        logger.info(f"=== [Plane 1] Initiating Sovereign Clinical Workflow for Study {study_id} ===")

        # Step 1: Execute Vertex AI reasoning engine directly
        analysis: ClinicalAnalysisResult = await self.engine.execute_clinical_reasoning_loop(
            study_id=study_id,
            cohort=cohort,
        )

        logger.info(
            f" [Plane 1] Analysis finished: Variance={analysis.variance_pct}%. "
            f"GxP Validation Hash: {analysis.gxp_validation_hash}"
        )

        # Step 2: Hand off to Plane 2 UI Bridge for Human-In-The-Loop review
        bridge_payload = {
            "studyId": analysis.study_id,
            "cohort": analysis.test_cohort,
            "variancePct": analysis.variance_pct,
            "clinicalFindings": analysis.clinical_findings,
            "recommendedAmendment": analysis.recommended_protocol_amendment,
        }

        dispatch_url = f"{self.bridge_url}/api/v1/bridge/dispatch-approval"
        logger.info(f" [Plane 1 -> Plane 2 Handshake] Dispatching approval card via {dispatch_url}...")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(dispatch_url, json=bridge_payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Bridge dispatch failed: {resp.status_code} - {resp.text}")
            bridge_data = resp.json()

        logger.info(
            f" [Plane 2] Approval Card successfully dispatched. Card ID: {bridge_data.get('cardId')}"
        )

        return {
            "plane1_analysis": analysis.model_dump(),
            "plane2_dispatch": bridge_data,
        }


if __name__ == "__main__":
    orchestrator = EnterpriseClinicalOrchestrator()
    result = asyncio.run(orchestrator.run_study_safety_workflow())
    print(result)
