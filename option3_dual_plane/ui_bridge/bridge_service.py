"""UI Bridge Service (Plane 2 Interaction Gateway).

Bridges Enterprise's sovereign backend execution plane (Plane 1) with the
interactive Human-in-the-Loop surface in Gemini Enterprise (Plane 2).
"""

from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any, Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from jose import jwt, JWTError

from backend.config import config
from .card_templates import render_approval_card
from option1_cloud_run_gateway.app.security import is_safe_webhook_url

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "service":"plane2-ui-bridge", "msg":"%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ui_bridge")

app = FastAPI(
    title="Enterprise Plane 2 UI Bridge Service",
    version="1.0.0",
    description="Demo bridge for a project-specific A2UI adapter workflow. Not a production control plane.",
)

# In-memory demo event log. This is not durable regulatory evidence.
AUDIT_TRAIL: List[Dict[str, Any]] = []
MAX_AUDIT_TRAIL = 1000
CONSUMED_JTIS: Dict[str, float] = {}
MAX_CONSUMED_JTIS = 5000


class DispatchApprovalRequest(BaseModel):
    studyId: str = Field(default="MK-3475-087")
    cohort: str = Field(default="Cohort-B")
    variancePct: float = Field(default=2.14)
    clinicalFindings: str
    recommendedAmendment: str
    geInboundUrl: Optional[str] = None


class ActionCallbackRequest(BaseModel):
    stateToken: str
    actionId: Optional[str] = None
    reviewerEmail: Optional[str] = Field(default=None, description="Demo display hint only; not trusted identity")


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "plane2-ui-bridge"}


@app.post("/api/v1/bridge/dispatch-approval")
async def dispatch_approval(req: DispatchApprovalRequest):
    """Receive completed analysis from Plane 1 and dispatch A2UI card to GE."""
    logger.info(f"[Bridge] Dispatching approval card for Study {req.studyId} ({req.cohort})")

    callback_url = f"{config.BRIDGE_SERVICE_URL}/api/v1/bridge/action-callback"

    # 1. Render A2UI Card with sealed state tokens
    card_data = render_approval_card(
        study_id=req.studyId,
        cohort=req.cohort,
        variance_pct=req.variancePct,
        findings=req.clinicalFindings,
        amendment=req.recommendedAmendment,
        callback_url=callback_url,
        secret_key=config.HMAC_SECRET,
    )

    # 2. Push card to Gemini Enterprise Inbound Receiver
    target_ge_url = req.geInboundUrl or f"{config.GE_INBOUND_URL}/api/v1/ge/inbound-webhook"
    logger.info(f"[Bridge] Pushing A2UI card to GE Inbound at: {target_ge_url}")

    # SSRF Guard: Validate target GE webhook URL
    safe, reason = is_safe_webhook_url(target_ge_url)
    if not safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insecure or prohibited GE webhook target (SSRF Guard): {reason}",
        )

    delivery_status = "DELIVERED"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(target_ge_url, json=card_data)
            logger.info(f"[Bridge] Pushed card to GE. Receiver status: {resp.status_code}")
    except Exception as exc:
        logger.warning(f"[Bridge] Could not deliver to live GE webhook ({str(exc)}). Continuing in standalone mode.")
        delivery_status = "SAVED_LOCAL"

    return {
        "status": "APPROVAL_CARD_PREPARED",
        "cardId": card_data["cardId"],
        "deliveryStatus": delivery_status,
        "a2ui": card_data["a2ui"],
        "stateTokens": card_data["tokens"],
    }


@app.post("/api/v1/bridge/action-callback")
async def action_callback(req: ActionCallbackRequest):
    """Consume a demo action token.

    No authenticated reviewer identity or legal electronic signature is asserted.
    """
    try:
        claims = jwt.decode(
            req.stateToken,
            config.HMAC_SECRET,
            algorithms=["HS256"],
            issuer="option3-plane2-demo-bridge",
            options={"require_exp": True, "require_iat": True, "require_iss": True},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired demo state token",
        ) from exc

    jti = str(claims.get("jti") or "")
    if not jti:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing replay-protection JTI")
    now_ts = datetime.now(timezone.utc).timestamp()
    expired = [key for key, exp in CONSUMED_JTIS.items() if exp < now_ts]
    for key in expired:
        CONSUMED_JTIS.pop(key, None)
    if jti in CONSUMED_JTIS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Demo action token already consumed")
    while len(CONSUMED_JTIS) >= MAX_CONSUMED_JTIS:
        CONSUMED_JTIS.pop(next(iter(CONSUMED_JTIS)), None)
    CONSUMED_JTIS[jti] = float(claims["exp"])

    study_id = claims.get("studyId")
    cohort = claims.get("cohort")
    decision = claims.get("decision")
    amendment = claims.get("amendment")
    now_utc = datetime.now(timezone.utc).isoformat()

    audit_entry = {
        "auditId": f"demo-audit-{len(AUDIT_TRAIL) + 1:04d}",
        "studyId": study_id,
        "cohort": cohort,
        "decision": decision,
        "amendment": amendment,
        "actor": "Demo reviewer (not authenticated)",
        "reviewerHint": req.reviewerEmail,
        "evidenceType": "JTI replay-protected demo action",
        "timestamp": now_utc,
        "regulatoryValidation": False,
        "persistence": "in-memory-demo",
        "jti": jti,
    }
    if len(AUDIT_TRAIL) >= MAX_AUDIT_TRAIL:
        AUDIT_TRAIL.pop(0)
    AUDIT_TRAIL.append(audit_entry)

    return {
        "status": "DEMO_DECISION_RECORDED",
        "decision": decision,
        "studyId": study_id,
        "cohort": cohort,
        "auditRecord": audit_entry,
    }


@app.get("/api/v1/bridge/audit-log")
async def get_audit_log():
    return {
        "count": len(AUDIT_TRAIL),
        "auditTrail": AUDIT_TRAIL,
        "persistence": "in-memory-demo",
        "regulatoryValidation": False,
    }
