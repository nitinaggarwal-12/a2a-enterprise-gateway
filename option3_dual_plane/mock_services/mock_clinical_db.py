"""Mock EDC / RWE (Real-World Evidence) Clinical Database.

Simulates Enterprise's internal clinical data warehouse containing patient cohort
adverse event tables for clinical trial MK-3475-087.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class SDTM_DM_Record(BaseModel):
    """CDISC SDTM Demographics Domain Record (DM)."""
    STUDYID: str = Field(..., description="Unique Study Identifier")
    DOMAIN: str = Field(default="DM")
    USUBJID: str = Field(..., description="Unique Subject Identifier")
    SUBJID: str = Field(..., description="Subject Identifier for the Study")
    RFSTDTC: Optional[str] = Field(None, description="Subject Reference Start Date/Time")
    AGE: Optional[int] = Field(None, description="Age at trial enrollment")
    SEX: str = Field(..., description="Sex: M / F / U")
    RACE: Optional[str] = Field(None, description="Race")
    ARMCD: str = Field(..., description="Planned Arm Code")


class SDTM_AE_Record(BaseModel):
    """CDISC SDTM Adverse Events Domain Record (AE)."""
    STUDYID: str = Field(..., description="Unique Study Identifier")
    DOMAIN: str = Field(default="AE")
    USUBJID: str = Field(..., description="Unique Subject Identifier")
    AETERM: str = Field(..., description="Reported Term for the Adverse Event")
    AEDECOD: str = Field(..., description="Dictionary-Derived Term (MedDRA)")
    AESEV: str = Field(..., description="Severity/Intensity: MILD / MODERATE / SEVERE")
    AESER: str = Field(default="N", description="Serious Event: Y / N")
    AESTDTC: Optional[str] = Field(None, description="Start Date/Time of Adverse Event")
    AEENDTC: Optional[str] = Field(None, description="End Date/Time of Adverse Event")
    AEREL: str = Field(default="POSSIBLE", description="Causality / Relationship to Study Drug")


class SDTM_LB_Record(BaseModel):
    """CDISC SDTM Laboratory Test Results Domain Record (LB)."""
    STUDYID: str = Field(...)
    DOMAIN: str = Field(default="LB")
    USUBJID: str = Field(...)
    LBTESTCD: str = Field(..., description="Lab Test Short Code, e.g. ALT, AST, BILI")
    LBTEST: str = Field(..., description="Lab Test Name")
    LBORRES: float = Field(..., description="Original Result Value")
    LBORRESU: str = Field(..., description="Original Result Units")
    LBNRIND: Optional[str] = Field(None, description="Normal Range Indicator: NORMAL / HIGH / LOW")


class SDTM_EX_Record(BaseModel):
    """CDISC SDTM Exposure Domain Record (EX)."""
    STUDYID: str = Field(...)
    DOMAIN: str = Field(default="EX")
    USUBJID: str = Field(...)
    EXTRT: str = Field(..., description="Name of Actual Treatment")
    EXDOSE: float = Field(..., description="Dose per Administration")
    EXDOSU: str = Field(default="mg", description="Dose Units")
    EXDOSFRQ: str = Field(default="Q3W", description="Dosing Frequency")
    EXSTDTC: Optional[str] = Field(None)


def validate_sdtm_record(domain: str, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate raw clinical dictionary against strict CDISC SDTM domain models."""
    domain_upper = domain.upper()
    model_map = {
        "DM": SDTM_DM_Record,
        "AE": SDTM_AE_Record,
        "LB": SDTM_LB_Record,
        "EX": SDTM_EX_Record,
    }
    model = model_map.get(domain_upper)
    if not model:
        return False, f"Unsupported CDISC SDTM domain: '{domain}'"

    try:
        model(**record)
        return True, None
    except Exception as exc:
        return False, str(exc)


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
