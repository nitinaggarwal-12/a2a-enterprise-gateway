"""Declarative A2UI Card Schemas for Clinical Dossier Approvals.

Plane 2 (Interaction Surface): Constructs clean, validated A2UI cards
with signed HMAC state tokens for Human-in-the-Loop decision capture.
"""

from typing import Any, Dict
from jose import jwt
from datetime import datetime, timezone, timedelta


def generate_hmac_token(payload: Dict[str, Any], secret: str, ttl_hours: int = 48) -> str:
    """Seal state payload in HMAC-SHA256 JWT for stateless validation."""
    now = datetime.now(timezone.utc)
    token_dict = dict(payload)
    token_dict.update({
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ttl_hours)).timestamp()),
        "iss": "Enterprise-plane2-bridge-service",
    })
    return jwt.encode(token_dict, secret, algorithm="HS256")


def render_approval_card(
    study_id: str,
    cohort: str,
    variance_pct: float,
    findings: str,
    amendment: str,
    callback_url: str,
    secret_key: str,
) -> Dict[str, Any]:
    """Render declarative A2UI approval card with sealed state tokens."""
    approve_token = generate_hmac_token(
        {
            "studyId": study_id,
            "cohort": cohort,
            "decision": "APPROVED",
            "amendment": amendment,
        },
        secret=secret_key,
    )

    reject_token = generate_hmac_token(
        {
            "studyId": study_id,
            "cohort": cohort,
            "decision": "REJECTED",
            "amendment": amendment,
        },
        secret=secret_key,
    )

    card_id = f"a2ui-card-{study_id}-{cohort}"

    a2ui_card = {
        "schemaVersion": "0.2.0",
        "surfaceType": "a2ui_card",
        "id": card_id,
        "title": f"Clinical Study Amendment Approval: {study_id}",
        "subtitle": f"Safety Review for Cohort {cohort} | Direct Vertex AI Execution",
        "badge": {
            "text": "HITL ACTION REQUIRED",
            "color": "amber",
        },
        "sections": [
            {
                "type": "metric_summary",
                "metrics": [
                    {"label": "Study Protocol", "value": study_id},
                    {"label": "Target Cohort", "value": cohort},
                    {"label": "Safety Variance", "value": f"+{variance_pct}%"},
                    {"label": "Demarcation", "value": "Plane 1 Vertex AI (Zero ADK Envelopes)"},
                ],
            },
            {
                "type": "narrative_box",
                "title": "Clinical Safety Evaluation",
                "body": findings,
            },
            {
                "type": "recommendation_box",
                "title": "Recommended Protocol Amendment",
                "body": amendment,
            },
        ],
        "actions": [
            {
                "id": "btn_approve_amendment",
                "label": "Authorize Protocol Amendment",
                "style": "SUCCESS",
                "actionEndpoint": callback_url,
                "stateToken": approve_token,
            },
            {
                "id": "btn_reject_amendment",
                "label": "Reject & Request Re-evaluation",
                "style": "DANGER",
                "actionEndpoint": callback_url,
                "stateToken": reject_token,
            },
        ],
    }

    return {
        "cardId": card_id,
        "a2ui": a2ui_card,
        "tokens": {
            "approve": approve_token,
            "reject": reject_token,
        },
    }
