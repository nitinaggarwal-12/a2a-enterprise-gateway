"""A2UI and Google Card v2 Surface Builder.

Generates dual-dialect Human-in-the-Loop (HITL) review cards (A2UI Flat JSON format
and Google Workspace Card v2 format) with cryptographically sealed action state tokens.
"""

from typing import Any, Dict, Optional
from .security import create_state_token


def build_clinical_review_surface(
    task_id: str,
    study_id: str,
    cohort: str,
    push_url: Optional[str] = None,
    protocol_version: str = "v4.2",
    variance_pct: float = 2.14,
    findings: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a dual-dialect A2UI and Google Card v2 surface for clinical dossier sign-off.

    Approve and Reject buttons contain signed state tokens with sealed context.
    """
    if findings is None:
        findings = (
            f"Cohort {cohort} shows adverse event rate increase of {variance_pct}%. "
            "Safety Review Committee recommends Phase 3 dose titration adjustment."
        )

    # Cryptographically seal state tokens for approve/reject actions
    approve_token = create_state_token({
        "taskId": task_id,
        "studyId": study_id,
        "cohort": cohort,
        "decision": "APPROVED",
        "protocolVersion": protocol_version,
        "pushUrl": push_url,
    })

    reject_token = create_state_token({
        "taskId": task_id,
        "studyId": study_id,
        "cohort": cohort,
        "decision": "REJECTED",
        "protocolVersion": protocol_version,
        "pushUrl": push_url,
    })

    # A2UI Flat Dialect Specification (v1.0.0)
    a2ui_flat = {
        "schemaVersion": "1.0.0",
        "surfaceType": "a2ui_card",
        "id": f"card-review-{task_id}",
        "header": {
            "title": f"Clinical Study Amendment Sign-off: {study_id}",
            "subtitle": f"Cohort {cohort} | Protocol {protocol_version} | 21 CFR Part 11 Audit Trail",
            "statusBadge": "PENDING_APPROVAL",
        },
        "sections": [
            {
                "type": "key_value_grid",
                "items": [
                    {"label": "Study Protocol", "value": study_id},
                    {"label": "Patient Cohort", "value": cohort},
                    {"label": "Safety Variance", "value": f"+{variance_pct}%"},
                    {"label": "GXP Compliance Level", "value": "Validated - GxP Class 1"},
                ],
            },
            {
                "type": "callout_box",
                "severity": "WARNING",
                "text": findings,
            },
        ],
        "actions": [
            {
                "id": "action_approve",
                "label": "Approve Study Amendment",
                "style": "PRIMARY",
                "actionType": "SUBMIT_STATE",
                "targetUrl": "/a2a/ui/action",
                "stateToken": approve_token,
            },
            {
                "id": "action_reject",
                "label": "Reject Amendment",
                "style": "DESTRUCTIVE",
                "actionType": "SUBMIT_STATE",
                "targetUrl": "/a2a/ui/action",
                "stateToken": reject_token,
            },
        ],
    }

    # Google Card v2 Dialect (for Google Chat / Gemini Enterprise Chat Card integration)
    google_card_v2 = {
        "cardId": f"card_{task_id}",
        "card": {
            "header": {
                "title": f"Clinical Study Amendment: {study_id}",
                "subtitle": f"Cohort {cohort} Review | Protocol {protocol_version}",
                "imageType": "SQUARE",
            },
            "sections": [
                {
                    "header": "Safety Committee Findings",
                    "widgets": [
                        {
                            "decoratedText": {
                                "topLabel": "Target Cohort",
                                "text": f"<b>Cohort {cohort}</b> (Variance: +{variance_pct}%)",
                            }
                        },
                        {
                            "textParagraph": {
                                "text": findings
                            }
                        },
                        {
                            "buttonList": {
                                "buttons": [
                                    {
                                        "text": "Approve Amendment",
                                        "color": {"red": 0.0, "green": 0.5, "blue": 0.2, "alpha": 1.0},
                                        "onClick": {
                                            "action": {
                                                "function": "handleA2UIAction",
                                                "parameters": [
                                                    {"key": "stateToken", "value": approve_token},
                                                    {"key": "taskId", "value": task_id},
                                                    {"key": "decision", "value": "APPROVED"},
                                                ],
                                            }
                                        },
                                    },
                                    {
                                        "text": "Reject Amendment",
                                        "color": {"red": 0.8, "green": 0.1, "blue": 0.1, "alpha": 1.0},
                                        "onClick": {
                                            "action": {
                                                "function": "handleA2UIAction",
                                                "parameters": [
                                                    {"key": "stateToken", "value": reject_token},
                                                    {"key": "taskId", "value": task_id},
                                                    {"key": "decision", "value": "REJECTED"},
                                                ],
                                            }
                                        },
                                    },
                                ]
                            }
                        },
                    ],
                }
            ],
        },
    }

    return {
        "a2ui": a2ui_flat,
        "googleCardV2": google_card_v2,
        "stateTokens": {
            "approve": approve_token,
            "reject": reject_token,
        },
    }
