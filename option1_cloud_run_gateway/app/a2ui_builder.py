"""A2UI and Omnichannel Enterprise Surface Builder & Transpiler.

Transpiles canonical A2UI (Agent-to-Agent UI v1.0.0) surfaces into 4 native enterprise targets:
1. Google Workspace Card v2 (Google Chat & Gemini Enterprise Chat Cards)
2. Web React / Glassmorphic Card (Native Tailwind/Alpine interactive DOM)
3. Slack Block Kit (Slack Enterprise Grid)
4. Microsoft Teams Adaptive Cards (v1.5)

Also provides biopharma regulated extensions:
- Double-Blind Role-Based Attribute Masking (DSMB unblinded vs blinded site monitor)
- Pharmacovigilance E2B(R3) 15-Day Expedited Reporting Clock Ticker
- Multi-Sig Sequential Sign-Off Chains (Biostatistician -> Medical Monitor -> QA Director)
- Declarative Sliders, Input Forms, and Sortable Clinical Data Grids
- 21 CFR Part 11 Stateless JTI Nonce-Guarded HMAC State Tokens
"""

import uuid
from typing import Any, Dict, List, Optional
from .security import create_state_token


def get_a2ui_preset_templates() -> Dict[str, Any]:
    """Return 4 production-grade A2UI biopharma preset templates."""
    task_dose = f"task-dose-{uuid.uuid4().hex[:8]}"
    token_dose_approve = create_state_token({
        "taskId": task_dose,
        "studyId": "MK-3475-087",
        "cohort": "Cohort-B",
        "decision": "APPROVED",
        "doseMg": 300,
        "role": "Medical Director",
        "protocolVersion": "v4.2",
    })
    token_dose_reject = create_state_token({
        "taskId": task_dose,
        "studyId": "MK-3475-087",
        "cohort": "Cohort-B",
        "decision": "REJECTED",
        "doseMg": 300,
        "role": "Medical Director",
        "protocolVersion": "v4.2",
    })

    task_pv = f"task-pv-{uuid.uuid4().hex[:8]}"
    token_pv_expedite = create_state_token({
        "taskId": task_pv,
        "caseId": "E2B-SUSAR-2026-0902",
        "urgency": "EXPEDITED_15_DAY",
        "decision": "DISPATCH_HEALTH_AUTHORITY",
        "role": "Pharmacovigilance Officer",
    })
    token_pv_downgrade = create_state_token({
        "taskId": task_pv,
        "caseId": "E2B-SUSAR-2026-0902",
        "urgency": "STANDARD_PERIODIC",
        "decision": "DOWNGRADE_TO_PERIODIC",
        "role": "Pharmacovigilance Officer",
    })

    task_gmp = f"task-gmp-{uuid.uuid4().hex[:8]}"
    token_gmp_approve = create_state_token({
        "taskId": task_gmp,
        "batchLot": "LOT-BIO-2026-881",
        "deviationCode": "DEV-PH-004",
        "decision": "RELEASE_BATCH_WITH_CAPA",
        "role": "QA Director",
    })
    token_gmp_quarantine = create_state_token({
        "taskId": task_gmp,
        "batchLot": "LOT-BIO-2026-881",
        "deviationCode": "DEV-PH-004",
        "decision": "QUARANTINE_BATCH",
        "role": "QA Director",
    })

    task_dev = f"task-dev-{uuid.uuid4().hex[:8]}"
    token_dev_approve = create_state_token({
        "taskId": task_dev,
        "studyId": "MK-3475-087",
        "subjectId": "US-101-0014",
        "decision": "APPROVE_DEVIATION_ACTION",
        "role": "Medical Safety Director",
    })
    token_dev_escalate = create_state_token({
        "taskId": task_dev,
        "studyId": "MK-3475-087",
        "subjectId": "US-101-0014",
        "decision": "ESCALATE_SAFETY_BOARD",
        "role": "Medical Safety Director",
    })

    return {
        "dose_titration": {
            "id": "dose_titration",
            "name": "Phase III Dose Titration & Toxicity Sign-Off",
            "description": "Interactive dosage slider with real-time Bayesian toxicity variance calculation and 21 CFR Part 11 approval buttons.",
            "category": "Clinical Safety",
            "a2ui": {
                "schemaVersion": "1.0.0",
                "surfaceType": "a2ui_card",
                "id": f"card-dose-{task_dose}",
                "header": {
                    "title": "Clinical Study Amendment: MK-3475-087",
                    "subtitle": "Cohort-B Dose Titration | Protocol v4.2 | 21 CFR Part 11 Electronic Signature",
                    "statusBadge": "PENDING_APPROVAL",
                    "avatarIcon": "fa-dna",
                },
                "sections": [
                    {
                        "type": "key_value_grid",
                        "title": "Study Parameters & Regulatory Boundaries",
                        "items": [
                            {"label": "Protocol Number", "value": "MK-3475-087"},
                            {"label": "Patient Population", "value": "Cohort-B (Advanced NSCLC, n=240)"},
                            {"label": "Current Baseline Dose", "value": "400 mg IV Q3W"},
                            {"label": "Regulatory Standard", "value": "21 CFR Part 11 / GxP Class 1"},
                        ],
                    },
                    {
                        "type": "interactive_slider",
                        "id": "dose_slider",
                        "label": "Proposed Dose Titration (mg)",
                        "min": 100,
                        "max": 400,
                        "step": 50,
                        "defaultValue": 300,
                        "unit": "mg",
                        "formula": "Toxicity = Baseline + 5.42 * (Dose/400)^1.8",
                        "impactMetrics": [
                            {"dose": 400, "toxicity": "10.02%", "delta": "+5.42%", "status": "EXCEEDED_THRESHOLD"},
                            {"dose": 300, "toxicity": "6.74%", "delta": "+2.14%", "status": "BORDERLINE_WARNING"},
                            {"dose": 250, "toxicity": "5.71%", "delta": "+1.11%", "status": "ACCEPTABLE"},
                            {"dose": 200, "toxicity": "4.90%", "delta": "+0.30%", "status": "OPTIMAL_SAFETY"},
                        ],
                    },
                    {
                        "type": "callout_box",
                        "severity": "WARNING",
                        "text": "Bayesian safety monitor flagged +2.14% elevation in Grade 3 ALT/AST metrics at 300mg. Recommended titration to 250mg or enhanced hepatic monitoring protocol.",
                    },
                    {
                        "type": "sequential_multisig",
                        "title": "21 CFR Part 11 Approval Chain",
                        "steps": [
                            {"role": "Lead Biostatistician", "name": "Dr. Elena Vance, PhD", "status": "APPROVED", "timestamp": "2026-09-03 14:12 UTC", "hash": "sig-hmac-vance-91f82"},
                            {"role": "Medical Monitor", "name": "Dr. R. Patel, MD", "status": "CURRENT_REVIEWER", "timestamp": "Awaiting Decision", "hash": "PENDING"},
                            {"role": "QA Director", "name": "Sarah Jenkins, RAC", "status": "AWAITING_PRIOR", "timestamp": "Queued", "hash": "QUEUED"},
                        ],
                    },
                ],
                "actions": [
                    {
                        "id": "action_approve_titration",
                        "label": "Sign & Approve Titration (300mg)",
                        "style": "PRIMARY",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_dose_approve,
                    },
                    {
                        "id": "action_reject_titration",
                        "label": "Reject Amendment",
                        "style": "DESTRUCTIVE",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_dose_reject,
                    },
                ],
            },
        },
        "pv_e2b_expedited": {
            "id": "pv_e2b_expedited",
            "name": "Pharmacovigilance E2B(R3) Expedited SUSAR Triage",
            "description": "15-day expedited reporting clock ticker, MedDRA v26.1 preferred terms, and health authority submission dispatch.",
            "category": "Pharmacovigilance",
            "a2ui": {
                "schemaVersion": "1.0.0",
                "surfaceType": "a2ui_card",
                "id": f"card-pv-{task_pv}",
                "header": {
                    "title": "E2B(R3) Expedited Safety Report: SUSAR-2026-0902",
                    "subtitle": "MedDRA v26.1 Serious Adverse Event | ICH E2A/E2B Compliance",
                    "statusBadge": "CRITICAL_ACTION_REQUIRED",
                    "avatarIcon": "fa-heart-pulse",
                },
                "sections": [
                    {
                        "type": "regulatory_clock",
                        "title": "FDA / EMA 15-Day Expedited Clock",
                        "deadlineHours": 360,
                        "hoursElapsed": 42,
                        "hoursRemaining": 318,
                        "displayString": "13d 06h remaining",
                        "status": "URGENT",
                        "regulatoryWindow": "15-Day Clock (SUSAR)",
                    },
                    {
                        "type": "key_value_grid",
                        "title": "Clinical ICSR Triage Summary",
                        "items": [
                            {"label": "Case Reference", "value": "E2B-SUSAR-2026-0902"},
                            {"label": "MedDRA PT", "value": "Autoimmune Hepatitis (PT 10003784)"},
                            {"label": "Seriousness Criteria", "value": "Hospitalization, Life-Threatening (Grade 4)"},
                            {"label": "Causality Assessment", "value": "Probable (Investigational Biologic)"},
                            {"label": "De-challenge / Re-challenge", "value": "Positive De-challenge (Dose held)"},
                            {"label": "Primary Suspect Drug", "value": "MK-1308 (Monoclonal IgG1)"},
                        ],
                    },
                    {
                        "type": "callout_box",
                        "severity": "CRITICAL",
                        "text": "ICH E2A Criteria Met: Unexpected Serious Adverse Reaction requires automated XML generation and transmission via AS2 Gateway to FDA ESG & EMA EudraVigilance.",
                    },
                ],
                "actions": [
                    {
                        "id": "action_dispatch_authorities",
                        "label": "Transmit Expedited E2B(R3) to FDA & EMA",
                        "style": "PRIMARY",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_pv_expedite,
                    },
                    {
                        "id": "action_downgrade_case",
                        "label": "Downgrade to Periodic PSUR",
                        "style": "SECONDARY",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_pv_downgrade,
                    },
                ],
            },
        },
        "lab_data_grid": {
            "id": "lab_data_grid",
            "name": "Multi-Cohort Clinical Laboratory Data Grid",
            "description": "Interactive sortable data table with double-blind role-based masking (DSMB unblinded vs blinded investigator).",
            "category": "Data Management",
            "a2ui": {
                "schemaVersion": "1.0.0",
                "surfaceType": "a2ui_card",
                "id": "card-lab-grid-001",
                "header": {
                    "title": "Central Laboratory Safety Grid: Protocol MK-3475-087",
                    "subtitle": "Liver Function Tests (ALT/AST/Total Bilirubin) | Visit 4 (Day 21)",
                    "statusBadge": "DOUBLE_BLIND_PROTECTED",
                    "avatarIcon": "fa-table-cells",
                },
                "sections": [
                    {
                        "type": "double_blind_banner",
                        "isBlinded": True,
                        "blindedMessage": "Double-Blind Masking ACTIVE. Subject IDs and treatment arms are cryptographically pseudonymized for Site Monitors. DSMB Unblinded Mode requires Medical Officer role.",
                    },
                    {
                        "type": "data_grid",
                        "title": "Laboratory Biomarkers (CTCAE v5.0 Grading)",
                        "columns": [
                            {"key": "subjectId", "label": "Subject ID", "sortable": True},
                            {"key": "treatmentArm", "label": "Treatment Arm", "sortable": True},
                            {"key": "visit", "label": "Visit Cycle", "sortable": False},
                            {"key": "altU_L", "label": "ALT (U/L)", "sortable": True},
                            {"key": "astU_L", "label": "AST (U/L)", "sortable": True},
                            {"key": "biliMg_dL", "label": "Total Bili (mg/dL)", "sortable": True},
                            {"key": "grade", "label": "CTCAE Grade", "sortable": True},
                        ],
                        "rows": [
                            {"subjectId": "SUBJ-001 [MASKED]", "unmaskedSubjectId": "US-101-0014", "treatmentArm": "Arm A [BLINDED]", "unmaskedArm": "MK-3475 400mg", "visit": "Cycle 1 Day 21", "altU_L": 142, "astU_L": 128, "biliMg_dL": 1.4, "grade": "Grade 2"},
                            {"subjectId": "SUBJ-002 [MASKED]", "unmaskedSubjectId": "US-101-0029", "treatmentArm": "Arm B [BLINDED]", "unmaskedArm": "Placebo Control", "visit": "Cycle 1 Day 21", "altU_L": 24, "astU_L": 22, "biliMg_dL": 0.6, "grade": "Grade 0"},
                            {"subjectId": "SUBJ-003 [MASKED]", "unmaskedSubjectId": "DE-202-0008", "treatmentArm": "Arm A [BLINDED]", "unmaskedArm": "MK-3475 400mg", "visit": "Cycle 1 Day 21", "altU_L": 284, "astU_L": 260, "biliMg_dL": 2.8, "grade": "Grade 3"},
                            {"subjectId": "SUBJ-004 [MASKED]", "unmaskedSubjectId": "JP-304-0012", "treatmentArm": "Arm A [BLINDED]", "unmaskedArm": "MK-3475 400mg", "visit": "Cycle 1 Day 21", "altU_L": 198, "astU_L": 175, "biliMg_dL": 1.9, "grade": "Grade 2"},
                            {"subjectId": "SUBJ-005 [MASKED]", "unmaskedSubjectId": "UK-401-0003", "treatmentArm": "Arm B [BLINDED]", "unmaskedArm": "Placebo Control", "visit": "Cycle 1 Day 21", "altU_L": 31, "astU_L": 29, "biliMg_dL": 0.7, "grade": "Grade 0"},
                        ],
                    },
                ],
                "actions": [
                    {
                        "id": "action_export_cdisc_lb",
                        "label": "Export CDISC LB Dataset (.XPT)",
                        "style": "PRIMARY",
                        "actionType": "DOWNLOAD_DATASET",
                        "targetUrl": "/api/cdisc/export/lb",
                    },
                ],
            },
        },
        "gmp_batch_capa": {
            "id": "gmp_batch_capa",
            "name": "GMP Biologics Batch Release & CAPA Sign-Off",
            "description": "Manufacturing deviation triage, root cause analysis, and 3-tier electronic signature release.",
            "category": "GMP Manufacturing",
            "a2ui": {
                "schemaVersion": "1.0.0",
                "surfaceType": "a2ui_card",
                "id": f"card-gmp-{task_gmp}",
                "header": {
                    "title": "GMP Batch Disposition: LOT-BIO-2026-881",
                    "subtitle": "Drug Substance Bulk Lot | Bioreactor 4B Temperature Excursion | CAPA-2026-11",
                    "statusBadge": "PENDING_QA_RELEASE",
                    "avatarIcon": "fa-vial-circle-check",
                },
                "sections": [
                    {
                        "type": "key_value_grid",
                        "title": "Batch Specifications & Excursion Details",
                        "items": [
                            {"label": "Lot Number", "value": "LOT-BIO-2026-881"},
                            {"label": "Product", "value": "Pembrolizumab Biosimilar Bulk (2000L)"},
                            {"label": "Deviation Reference", "value": "DEV-PH-004 (Minor Temp Delta)"},
                            {"label": "Excursion Extent", "value": "+1.2°C for 22 minutes (Limit: +/- 1.5°C)"},
                            {"label": "CQA Impact Analysis", "value": "Purity: 99.1% (Spec: >98.0%), Potency: 104%"},
                            {"label": "GAMP 5 Classification", "value": "Category 4 Configured Software"},
                        ],
                    },
                    {
                        "type": "callout_box",
                        "severity": "INFO",
                        "text": "Technical Assessment Conclusion: Critical Quality Attributes (CQAs) remain within validated specification limits. Batch release recommended under active CAPA-2026-11 sensor recalibration.",
                    },
                ],
                "actions": [
                    {
                        "id": "action_qa_release",
                        "label": "21 CFR Part 11 Electronic Batch Release",
                        "style": "PRIMARY",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_gmp_approve,
                    },
                    {
                        "id": "action_quarantine",
                        "label": "Quarantine Batch for Investigation",
                        "style": "DESTRUCTIVE",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_gmp_quarantine,
                    },
                ],
            },
        },
        "protocol_deviation_triage": {
            "id": "protocol_deviation_triage",
            "name": "Clinical Protocol Deviation & Overdose Triage",
            "description": "Interactive GxP form controls: text input for medical justification, dropdown for deviation classification, radio buttons for subject action, and scheduled amendment date picker.",
            "category": "Clinical Operations",
            "a2ui": {
                "schemaVersion": "1.0.0",
                "surfaceType": "a2ui_card",
                "id": f"card-deviation-{task_dev}",
                "header": {
                    "title": "Protocol Deviation Triage: Study MK-3475-087",
                    "subtitle": "Subject US-101-0014 | Site 101 (Boston Clinical Research) | 21 CFR Part 11",
                    "statusBadge": "DEVIATION_PENDING_REVIEW",
                    "avatarIcon": "fa-clipboard-check",
                },
                "sections": [
                    {
                        "type": "key_value_grid",
                        "title": "Reported Deviation Parameters",
                        "items": [
                            {"label": "Study Protocol", "value": "MK-3475-087"},
                            {"label": "Subject ID", "value": "US-101-0014 (Cohort-B)"},
                            {"label": "Site Location", "value": "Site 101 - Boston Clinical"},
                            {"label": "Incident Nature", "value": "Accidental Dose Excursion (450mg vs 300mg assigned)"},
                        ],
                    },
                    {
                        "type": "callout_box",
                        "severity": "WARNING",
                        "text": "GxP Deviation Alert: Subject received 150mg excess dose during Cycle 2 Day 1 administration. Vital signs stable; immediate medical monitor disposition required within 24h per ICH GCP E6(R2).",
                    },
                    {
                        "type": "dropdown_select",
                        "id": "deviation_severity",
                        "name": "deviationSeverity",
                        "label": "Deviation Severity Classification",
                        "placeholder": "Select severity tier...",
                        "defaultValue": "Major",
                        "options": [
                            {"label": "Minor (No Subject Safety Impact)", "value": "Minor"},
                            {"label": "Major (Potential Safety Impact)", "value": "Major"},
                            {"label": "Critical (ICH GCP Integrity Breach)", "value": "Critical"},
                        ],
                    },
                    {
                        "type": "radio_group",
                        "id": "recommended_action",
                        "name": "recommendedAction",
                        "label": "Clinical Trial Committee Recommended Action",
                        "defaultValue": "Maintain Patient on Reduced Dose",
                        "options": [
                            {"label": "Maintain Patient on Reduced Dose (250mg)", "value": "Maintain Patient on Reduced Dose"},
                            {"label": "Temporarily Hold Treatment Pending PK Labs", "value": "Hold Treatment"},
                            {"label": "Discontinue Subject from Investigational Product", "value": "Discontinue Subject"},
                        ],
                    },
                    {
                        "type": "text_input",
                        "id": "justification_rationale",
                        "name": "justificationRationale",
                        "label": "Medical Director Justification & Clinical Rationale (21 CFR Part 11 § 11.50)",
                        "multiline": True,
                        "placeholder": "Enter detailed clinical rationale, safety monitoring plan, and institutional IRB/IEC notification summary...",
                        "defaultValue": "Subject exhibited transient Grade 1 nausea with normal AST/ALT liver enzymes. Safety profile permits continuation with weekly hepatic biomarker surveillance.",
                    },
                    {
                        "type": "date_picker",
                        "id": "follow_up_date",
                        "name": "followUpDate",
                        "label": "Mandatory Follow-Up Safety Assessment Date",
                        "defaultValue": "2026-09-12",
                    },
                ],
                "actions": [
                    {
                        "id": "action_approve_deviation",
                        "label": "Sign & Submit GxP Deviation Triage",
                        "style": "PRIMARY",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_dev_approve,
                    },
                    {
                        "id": "action_escalate_safety",
                        "label": "Escalate to Global Safety Board",
                        "style": "DESTRUCTIVE",
                        "actionType": "SUBMIT_STATE",
                        "targetUrl": "/a2a/ui/action",
                        "stateToken": token_dev_escalate,
                    },
                ],
            },
        },
    }


def transpile_a2ui_to_google_card_v2(a2ui_card: Dict[str, Any], unblind: bool = False) -> Dict[str, Any]:
    """Transpile canonical A2UI card into Google Workspace Card v2 format (for Google Chat / Gemini Enterprise)."""
    if isinstance(a2ui_card.get("a2ui"), dict):
        a2ui_card = a2ui_card["a2ui"]
    header = a2ui_card.get("header", {})
    sections = a2ui_card.get("sections", [])
    actions = a2ui_card.get("actions", [])
    card_id = a2ui_card.get("id", f"card_{uuid.uuid4().hex[:8]}")

    google_sections = []

    for sec in sections:
        sec_type = sec.get("type")
        sec_title = sec.get("title", "")
        widgets = []

        if sec_type == "key_value_grid":
            for item in sec.get("items", []):
                widgets.append({
                    "decoratedText": {
                        "topLabel": item.get("label", ""),
                        "text": f"<b>{item.get('value', '')}</b>",
                    }
                })

        elif sec_type == "callout_box":
            severity = sec.get("severity", "INFO")
            icon = "⚠️" if severity in ["WARNING", "CRITICAL"] else "ℹ️"
            widgets.append({
                "textParagraph": {
                    "text": f"{icon} <b>[{severity}]</b> {sec.get('text', '')}"
                }
            })

        elif sec_type == "interactive_slider":
            widgets.append({
                "decoratedText": {
                    "topLabel": sec.get("label", "Dose Titration"),
                    "text": f"<b>Selected: {sec.get('defaultValue')} {sec.get('unit')}</b> (Range: {sec.get('min')} - {sec.get('max')} {sec.get('unit')})",
                }
            })
            if "formula" in sec:
                widgets.append({
                    "textParagraph": {
                        "text": f"<i>Mathematical Model: {sec.get('formula')}</i>"
                    }
                })

        elif sec_type == "regulatory_clock":
            widgets.append({
                "decoratedText": {
                    "topLabel": sec.get("regulatoryWindow", "Regulatory Clock"),
                    "text": f"<font color=\"#d9381e\"><b>⏱️ {sec.get('displayString')}</b></font> ({sec.get('hoursRemaining')}h remaining)",
                }
            })

        elif sec_type == "double_blind_banner":
            msg = sec.get("blindedMessage", "")
            if unblind:
                msg = "🔓 DSMB UNBLINDED ACCESS GRANTED: Subject identifiers and randomized arms revealed."
            widgets.append({
                "textParagraph": {
                    "text": f"<b>[Security Boundary]</b> {msg}"
                }
            })

        elif sec_type == "data_grid":
            rows = sec.get("rows", [])
            for r in rows[:4]:
                subj = r.get("unmaskedSubjectId") if unblind else r.get("subjectId")
                arm = r.get("unmaskedArm") if unblind else r.get("treatmentArm")
                alt = r.get("altU_L")
                ast = r.get("astU_L")
                grade = r.get("grade")
                widgets.append({
                    "decoratedText": {
                        "topLabel": f"Patient: {subj} | {arm}",
                        "text": f"ALT: <b>{alt} U/L</b> | AST: <b>{ast} U/L</b> | Grade: <b>{grade}</b>",
                    }
                })

        elif sec_type == "sequential_multisig":
            for step in sec.get("steps", []):
                status_icon = "✅" if step.get("status") == "APPROVED" else ("⏳" if step.get("status") == "CURRENT_REVIEWER" else "🔒")
                widgets.append({
                    "decoratedText": {
                        "topLabel": f"{status_icon} {step.get('role')}: {step.get('name')}",
                        "text": f"Status: <b>{step.get('status')}</b> | Stamp: <code>{step.get('hash')}</code>",
                    }
                })

        elif sec_type == "text_input":
            is_multiline = sec.get("multiline", False)
            widgets.append({
                "textInput": {
                    "name": sec.get("name", sec.get("id", "text_input")),
                    "label": sec.get("label", "Enter value"),
                    "type": "MULTIPLE_LINE" if is_multiline else "SINGLE_LINE",
                    "hintText": sec.get("placeholder", ""),
                    "value": sec.get("defaultValue", ""),
                }
            })

        elif sec_type == "dropdown_select":
            items = []
            for opt in sec.get("options", []):
                items.append({
                    "text": opt.get("label", opt.get("text", "")),
                    "value": opt.get("value", ""),
                    "selected": opt.get("value") == sec.get("defaultValue", ""),
                })
            widgets.append({
                "selectionInput": {
                    "name": sec.get("name", sec.get("id", "select_input")),
                    "label": sec.get("label", "Select an option"),
                    "type": "DROPDOWN",
                    "items": items,
                }
            })

        elif sec_type == "radio_group":
            items = []
            for opt in sec.get("options", []):
                items.append({
                    "text": opt.get("label", opt.get("text", "")),
                    "value": opt.get("value", ""),
                    "selected": opt.get("value") == sec.get("defaultValue", ""),
                })
            widgets.append({
                "selectionInput": {
                    "name": sec.get("name", sec.get("id", "radio_input")),
                    "label": sec.get("label", "Choose option"),
                    "type": "RADIO_BUTTON",
                    "items": items,
                }
            })

        elif sec_type == "date_picker":
            widgets.append({
                "dateTimePicker": {
                    "name": sec.get("name", sec.get("id", "date_input")),
                    "label": sec.get("label", "Select Date"),
                    "type": "DATE_ONLY",
                }
            })

        if widgets:
            g_sec = {"widgets": widgets}
            if sec_title:
                g_sec["header"] = sec_title
            google_sections.append(g_sec)

    if actions:
        button_widgets = []
        for act in actions:
            is_destructive = act.get("style") == "DESTRUCTIVE"
            is_primary = act.get("style") == "PRIMARY"
            color = (
                {"red": 0.85, "green": 0.15, "blue": 0.15, "alpha": 1.0}
                if is_destructive
                else ({"red": 0.0, "green": 0.52, "blue": 0.48, "alpha": 1.0} if is_primary else None)
            )

            btn = {
                "text": act.get("label", "Action"),
                "onClick": {
                    "action": {
                        "function": "handleA2UIAction",
                        "parameters": [
                            {"key": "actionId", "value": act.get("id", "")},
                            {"key": "stateToken", "value": act.get("stateToken", "")},
                            {"key": "targetUrl", "value": act.get("targetUrl", "/a2a/ui/action")},
                        ],
                    }
                },
            }
            if color:
                btn["color"] = color
            button_widgets.append(btn)

        google_sections.append({
            "header": "Human-in-the-Loop Sign-Off (21 CFR Part 11)",
            "widgets": [{"buttonList": {"buttons": button_widgets}}],
        })

    return {
        "cardId": card_id,
        "card": {
            "header": {
                "title": header.get("title", "A2A Workflow Notification"),
                "subtitle": header.get("subtitle", "Google Agent-to-Agent Gateway"),
                "imageType": "SQUARE",
            },
            "sections": google_sections,
        },
    }


def transpile_a2ui_to_slack_block_kit(a2ui_card: Dict[str, Any], unblind: bool = False) -> Dict[str, Any]:
    """Transpile canonical A2UI card into Slack Enterprise Grid Block Kit dialect."""
    if isinstance(a2ui_card.get("a2ui"), dict):
        a2ui_card = a2ui_card["a2ui"]
    header = a2ui_card.get("header", {})
    sections = a2ui_card.get("sections", [])
    actions = a2ui_card.get("actions", [])

    blocks: List[Dict[str, Any]] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header.get("title", "Clinical Action Required")[:150],
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{header.get('subtitle', '')}*\nStatus: `{header.get('statusBadge', 'PENDING')}`",
            },
        },
        {"type": "divider"},
    ]

    for sec in sections:
        sec_type = sec.get("type")
        sec_title = sec.get("title", "")

        if sec_type == "key_value_grid":
            items = sec.get("items", [])
            fields = [
                {"type": "mrkdwn", "text": f"*{it.get('label')}:*\n{it.get('value')}"}
                for it in items[:10]
            ]
            block = {"type": "section", "fields": fields}
            if sec_title:
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*{sec_title}*"}})
            blocks.append(block)

        elif sec_type == "callout_box":
            severity = sec.get("severity", "INFO")
            icon = "⚠️" if severity in ["WARNING", "CRITICAL"] else "ℹ️"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"> {icon} *[{severity} Notice]*\n> {sec.get('text', '')}",
                },
            })

        elif sec_type == "interactive_slider":
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🎚️ *{sec.get('label')}*: `{sec.get('defaultValue')} {sec.get('unit')}`\nRange: {sec.get('min')} - {sec.get('max')} {sec.get('unit')} | _Model: {sec.get('formula', '')}_",
                },
            })

        elif sec_type == "regulatory_clock":
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *{sec.get('regulatoryWindow', 'Regulatory Clock')}*\n*Remaining:* `{sec.get('displayString')}` ({sec.get('hoursRemaining')}h left)\nStatus: *{sec.get('status')}*",
                },
            })

        elif sec_type == "data_grid":
            rows = sec.get("rows", [])
            grid_text = "*Clinical Biomarker Grid:*\n"
            for r in rows[:4]:
                subj = r.get("unmaskedSubjectId") if unblind else r.get("subjectId")
                arm = r.get("unmaskedArm") if unblind else r.get("treatmentArm")
                grid_text += f"• `{subj}` ({arm}): ALT *{r.get('altU_L')} U/L*, AST *{r.get('astU_L')} U/L* [{r.get('grade')}]\n"
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": grid_text}})

        elif sec_type == "sequential_multisig":
            ms_text = f"*{sec.get('title', 'Approval Chain')}:*\n"
            for s in sec.get("steps", []):
                icon = "✅" if s.get("status") == "APPROVED" else ("⏳" if s.get("status") == "CURRENT_REVIEWER" else "🔒")
                ms_text += f"{icon} *{s.get('role')}* ({s.get('name')}): `{s.get('status')}`\n"
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": ms_text}})

        elif sec_type == "text_input":
            is_multiline = sec.get("multiline", False)
            blocks.append({
                "type": "input",
                "block_id": f"block_{sec.get('id', 'text')}",
                "label": {"type": "plain_text", "text": sec.get("label", "Input")[:75]},
                "element": {
                    "type": "plain_text_input",
                    "action_id": sec.get("name", sec.get("id", "input_field")),
                    "multiline": is_multiline,
                    "placeholder": {"type": "plain_text", "text": sec.get("placeholder", "Enter text")[:75]},
                },
                "optional": sec.get("optional", True),
            })

        elif sec_type == "dropdown_select":
            options = []
            for opt in sec.get("options", []):
                options.append({
                    "text": {"type": "plain_text", "text": opt.get("label", opt.get("text", ""))[:75]},
                    "value": opt.get("value", ""),
                })
            blocks.append({
                "type": "input",
                "block_id": f"block_{sec.get('id', 'select')}",
                "label": {"type": "plain_text", "text": sec.get("label", "Select Option")[:75]},
                "element": {
                    "type": "static_select",
                    "action_id": sec.get("name", sec.get("id", "select_field")),
                    "placeholder": {"type": "plain_text", "text": sec.get("placeholder", "Choose option")[:75]},
                    "options": options[:100],
                },
                "optional": sec.get("optional", True),
            })

        elif sec_type == "radio_group":
            options = []
            for opt in sec.get("options", []):
                options.append({
                    "text": {"type": "plain_text", "text": opt.get("label", opt.get("text", ""))[:75]},
                    "value": opt.get("value", ""),
                })
            blocks.append({
                "type": "input",
                "block_id": f"block_{sec.get('id', 'radio')}",
                "label": {"type": "plain_text", "text": sec.get("label", "Options")[:75]},
                "element": {
                    "type": "radio_buttons",
                    "action_id": sec.get("name", sec.get("id", "radio_field")),
                    "options": options[:100],
                },
                "optional": sec.get("optional", True),
            })

        elif sec_type == "date_picker":
            blocks.append({
                "type": "input",
                "block_id": f"block_{sec.get('id', 'date')}",
                "label": {"type": "plain_text", "text": sec.get("label", "Select Date")[:75]},
                "element": {
                    "type": "datepicker",
                    "action_id": sec.get("name", sec.get("id", "date_field")),
                    "placeholder": {"type": "plain_text", "text": "Select a date"},
                },
                "optional": sec.get("optional", True),
            })

    if actions:
        elements = []
        for act in actions:
            style = "primary" if act.get("style") == "PRIMARY" else ("danger" if act.get("style") == "DESTRUCTIVE" else None)
            btn = {
                "type": "button",
                "text": {"type": "plain_text", "text": act.get("label", "Action")[:75]},
                "action_id": act.get("id", "btn_action"),
                "value": act.get("stateToken", ""),
            }
            if style:
                btn["style"] = style
            elements.append(btn)

        blocks.append({"type": "divider"})
        blocks.append({"type": "actions", "elements": elements})

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🔒 *21 CFR Part 11 Stateless JTI Nonce Guard* | Sealed by Google A2A Gateway v1.0.0",
            }
        ],
    })

    return {
        "text": header.get("title", "A2A Workflow Update"),
        "blocks": blocks,
    }


def transpile_a2ui_to_teams_adaptive_card(a2ui_card: Dict[str, Any], unblind: bool = False) -> Dict[str, Any]:
    """Transpile canonical A2UI card into Microsoft Teams Adaptive Cards (v1.5) schema."""
    if isinstance(a2ui_card.get("a2ui"), dict):
        a2ui_card = a2ui_card["a2ui"]
    header = a2ui_card.get("header", {})
    sections = a2ui_card.get("sections", [])
    actions = a2ui_card.get("actions", [])

    body: List[Dict[str, Any]] = [
        {
            "type": "Container",
            "style": "emphasis",
            "items": [
                {
                    "type": "TextBlock",
                    "text": header.get("title", "A2A Workflow Review"),
                    "weight": "Bolder",
                    "size": "Large",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": header.get("subtitle", ""),
                    "spacing": "None",
                    "isSubtle": True,
                    "wrap": True,
                },
            ],
        }
    ]

    for sec in sections:
        sec_type = sec.get("type")
        sec_title = sec.get("title", "")

        if sec_type == "key_value_grid":
            if sec_title:
                body.append({"type": "TextBlock", "text": sec_title, "weight": "Bolder", "spacing": "Medium"})
            facts = [
                {"title": it.get("label", ""), "value": str(it.get("value", ""))}
                for it in sec.get("items", [])
            ]
            body.append({"type": "FactSet", "facts": facts})

        elif sec_type == "callout_box":
            severity = sec.get("severity", "INFO")
            body.append({
                "type": "Container",
                "style": "warning" if severity in ["WARNING", "CRITICAL"] else "accent",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"⚠️ [{severity}] {sec.get('text', '')}",
                        "wrap": True,
                    }
                ],
            })

        elif sec_type == "interactive_slider":
            body.append({
                "type": "TextBlock",
                "text": f"🎚️ {sec.get('label')}: {sec.get('defaultValue')} {sec.get('unit')}",
                "weight": "Bolder",
            })
            body.append({
                "type": "Input.Number",
                "id": sec.get("id", "doseInput"),
                "min": sec.get("min", 100),
                "max": sec.get("max", 400),
                "value": sec.get("defaultValue", 300),
                "placeholder": f"Enter value ({sec.get('unit')})",
            })

        elif sec_type == "regulatory_clock":
            body.append({
                "type": "Container",
                "style": "attention",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"⏱️ {sec.get('regulatoryWindow')}: {sec.get('displayString')}",
                        "weight": "Bolder",
                        "color": "Attention",
                    }
                ],
            })

        elif sec_type == "data_grid":
            rows = sec.get("rows", [])
            facts = []
            for r in rows[:4]:
                subj = r.get("unmaskedSubjectId") if unblind else r.get("subjectId")
                arm = r.get("unmaskedArm") if unblind else r.get("treatmentArm")
                facts.append({
                    "title": f"{subj} ({arm})",
                    "value": f"ALT {r.get('altU_L')} U/L | AST {r.get('astU_L')} U/L | {r.get('grade')}",
                })
            body.append({"type": "FactSet", "facts": facts})

        elif sec_type == "sequential_multisig":
            ms_facts = [
                {"title": f"{s.get('role')} ({s.get('name')})", "value": f"{s.get('status')} [{s.get('hash')}]"}
                for s in sec.get("steps", [])
            ]
            body.append({"type": "FactSet", "facts": ms_facts})

        elif sec_type == "text_input":
            body.append({
                "type": "Input.Text",
                "id": sec.get("name", sec.get("id", "textInput")),
                "label": sec.get("label", "Text Input"),
                "placeholder": sec.get("placeholder", ""),
                "isMultiline": sec.get("multiline", False),
                "value": sec.get("defaultValue", ""),
                "isRequired": not sec.get("optional", True),
            })

        elif sec_type == "dropdown_select":
            choices = [
                {"title": opt.get("label", opt.get("text", "")), "value": opt.get("value", "")}
                for opt in sec.get("options", [])
            ]
            body.append({
                "type": "Input.ChoiceSet",
                "id": sec.get("name", sec.get("id", "dropdownSelect")),
                "label": sec.get("label", "Select Option"),
                "placeholder": sec.get("placeholder", "Choose option"),
                "style": "compact",
                "value": sec.get("defaultValue", ""),
                "choices": choices,
                "isRequired": not sec.get("optional", True),
            })

        elif sec_type == "radio_group":
            choices = [
                {"title": opt.get("label", opt.get("text", "")), "value": opt.get("value", "")}
                for opt in sec.get("options", [])
            ]
            body.append({
                "type": "Input.ChoiceSet",
                "id": sec.get("name", sec.get("id", "radioGroup")),
                "label": sec.get("label", "Select Option"),
                "style": "expanded",
                "value": sec.get("defaultValue", ""),
                "choices": choices,
                "isRequired": not sec.get("optional", True),
            })

        elif sec_type == "date_picker":
            body.append({
                "type": "Input.Date",
                "id": sec.get("name", sec.get("id", "datePicker")),
                "label": sec.get("label", "Select Date"),
                "value": sec.get("defaultValue", ""),
                "isRequired": not sec.get("optional", True),
            })

    teams_actions = []
    for act in actions:
        teams_actions.append({
            "type": "Action.Submit",
            "title": act.get("label", "Execute"),
            "style": "positive" if act.get("style") == "PRIMARY" else ("destructive" if act.get("style") == "DESTRUCTIVE" else "default"),
            "data": {
                "actionId": act.get("id"),
                "stateToken": act.get("stateToken"),
                "targetUrl": act.get("targetUrl", "/a2a/ui/action"),
            },
        })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": body,
        "actions": teams_actions,
    }


def transpile_a2ui_to_web_glassmorphic(a2ui_card: Dict[str, Any], unblind: bool = False) -> Dict[str, Any]:
    """Transpile canonical A2UI card into Web Glassmorphic card descriptor for high-craft web rendering."""
    inner = a2ui_card.get("a2ui") if isinstance(a2ui_card.get("a2ui"), dict) else a2ui_card
    card = dict(inner)
    card["unblindedView"] = unblind
    card["transpiledAt"] = "2026-09-04T00:00:00Z"
    card["targetFramework"] = "Tailwind CSS + Alpine.js v3 + 21 CFR Part 11 Web Component"

    for sec in card.get("sections", []):
        if sec.get("type") == "data_grid" and unblind:
            sec_copy = dict(sec)
            for r in sec_copy.get("rows", []):
                r["displaySubjectId"] = r.get("unmaskedSubjectId", r.get("subjectId"))
                r["displayArm"] = r.get("unmaskedArm", r.get("treatmentArm"))
        elif sec.get("type") == "double_blind_banner":
            sec["isBlinded"] = not unblind

    return card


def transpile_a2ui_to_all(a2ui_card: Dict[str, Any], unblind: bool = False) -> Dict[str, Any]:
    """Omnichannel transpilation: returns all 4 enterprise dialects synchronously."""
    inner_card = a2ui_card.get("a2ui") if isinstance(a2ui_card.get("a2ui"), dict) else a2ui_card
    canonical = dict(a2ui_card)
    if isinstance(inner_card, dict):
        for k in ["header", "sections", "actions"]:
            if k in inner_card:
                canonical[k] = inner_card[k]

    return {
        "canonicalA2UI": canonical,
        "googleCardV2": transpile_a2ui_to_google_card_v2(a2ui_card, unblind=unblind),
        "slackBlockKit": transpile_a2ui_to_slack_block_kit(a2ui_card, unblind=unblind),
        "teamsAdaptiveCard": transpile_a2ui_to_teams_adaptive_card(a2ui_card, unblind=unblind),
        "webGlassmorphic": transpile_a2ui_to_web_glassmorphic(a2ui_card, unblind=unblind),
        "dialects": ["google_card_v2", "slack_block_kit", "teams_adaptive_card", "web_glassmorphic"],
        "isUnblinded": unblind,
        "schemaVersion": "1.0.0",
        "gxpAudited": True,
    }


def build_clinical_review_surface(
    task_id: str,
    study_id: str,
    cohort: str,
    push_url: Optional[str] = None,
    protocol_version: str = "v4.2",
    variance_pct: float = 2.14,
    findings: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a dual-dialect A2UI and Google Card v2 surface with JTI nonce-guarded state tokens."""
    if findings is None:
        findings = (
            f"Cohort {cohort} shows adverse event rate increase of {variance_pct}%. "
            "Safety Review Committee recommends Phase 3 dose titration adjustment."
        )

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

    all_dialects = transpile_a2ui_to_all(a2ui_flat)

    return {
        "a2ui": a2ui_flat,
        "googleCardV2": all_dialects["googleCardV2"],
        "slackBlockKit": all_dialects["slackBlockKit"],
        "teamsAdaptiveCard": all_dialects["teamsAdaptiveCard"],
        "webGlassmorphic": all_dialects["webGlassmorphic"],
        "stateTokens": {
            "approve": approve_token,
            "reject": reject_token,
        },
    }

