"""Mock EDC / RWE (Real-World Evidence) Clinical Database.

Simulates Enterprise's internal clinical data warehouse containing patient cohort
adverse event tables for clinical trial MK-3475-087.
"""

from typing import Any, Dict, List


CLINICAL_REGISTRY_DATA: Dict[str, Dict[str, Any]] = {
    "MK-3475-087": {
        "studyName": "Phase 3 Keytruda Combination in Advanced Solid Tumors",
        "protocolVersion": "v4.2",
        "cohorts": {
            "Cohort-A": {
                "enrolled": 240,
                "dosage": "200mg Q3W",
                "adverseEvents": [
                    {"preferredTerm": "Fatigue", "grade": 1, "count": 48, "rate": 0.20},
                    {"preferredTerm": "Nausea", "grade": 2, "count": 36, "rate": 0.15},
                    {"preferredTerm": "ALT Elevation", "grade": 3, "count": 6, "rate": 0.025},
                    {"preferredTerm": "AST Elevation", "grade": 3, "count": 5, "rate": 0.0208},
                ],
                "totalGrade3PlusEvents": 11,
                "overallGrade3Rate": 0.0458,
            },
            "Cohort-B": {
                "enrolled": 240,
                "dosage": "400mg Q6W (High Dose Escalation)",
                "adverseEvents": [
                    {"preferredTerm": "Fatigue", "grade": 2, "count": 52, "rate": 0.216},
                    {"preferredTerm": "Nausea", "grade": 2, "count": 41, "rate": 0.170},
                    {"preferredTerm": "ALT Elevation", "grade": 3, "count": 12, "rate": 0.050},
                    {"preferredTerm": "AST Elevation", "grade": 3, "count": 10, "rate": 0.0416},
                    {"preferredTerm": "Immune-Mediated Hepatitis", "grade": 4, "count": 2, "rate": 0.0083},
                ],
                "totalGrade3PlusEvents": 24,
                "overallGrade3Rate": 0.1000,
            },
        },
    }
}


def query_clinical_study_data(study_id: str, cohort: str) -> Dict[str, Any]:
    """Retrieve structured adverse event table for a study and cohort."""
    study = CLINICAL_REGISTRY_DATA.get(study_id)
    if not study:
        return {"error": f"Study {study_id} not found in EDC registry"}

    cohort_data = study["cohorts"].get(cohort)
    if not cohort_data:
        return {"error": f"Cohort {cohort} not found for Study {study_id}"}

    return {
        "studyId": study_id,
        "studyName": study["studyName"],
        "protocolVersion": study["protocolVersion"],
        "cohort": cohort,
        "data": cohort_data,
    }


def compute_adverse_event_variance(study_id: str, baseline_cohort: str = "Cohort-A", test_cohort: str = "Cohort-B") -> Dict[str, Any]:
    """Compute statistical variance and risk differential between cohorts."""
    study = CLINICAL_REGISTRY_DATA.get(study_id, {})
    cohorts = study.get("cohorts", {})

    base = cohorts.get(baseline_cohort, {})
    test = cohorts.get(test_cohort, {})

    if not base or not test:
        return {"error": "Invalid cohorts for variance comparison"}

    base_rate = base.get("overallGrade3Rate", 0.0)
    test_rate = test.get("overallGrade3Rate", 0.0)
    variance_pct = round((test_rate - base_rate) * 100, 2)

    return {
        "studyId": study_id,
        "baselineCohort": baseline_cohort,
        "testCohort": test_cohort,
        "baselineGrade3Rate": base_rate,
        "testGrade3Rate": test_rate,
        "variancePct": variance_pct,
        "significance": "p < 0.01 (Statistically Significant)",
        "recommendedAction": "Dose Titration Safety Amendment Required (Protocol v4.2 -> v4.3)",
    }
