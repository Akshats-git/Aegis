"""The clinical data model for Aegis.

Every clinical fact carries two things that make Aegis a *safety* tool rather than a
filing cabinet:

  status  — is this true RIGHT NOW? (active) or is it stale? (discontinued/resolved/
            corrected). Stale facts are what get patients hurt, so we track it explicitly.
  source  — which document did this come from? Every fact is traceable, so a new doctor
            can trust the summary. (Surfaced via Cognee's evidence references.)

These map onto nodes in the Cognee knowledge graph; the temporal fields (started/stopped,
onset/resolved) let Cognee reason over *when* things were true.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ClinicalStatus(str, Enum):
    ACTIVE = "active"              # currently true — safe to act on
    DISCONTINUED = "discontinued"  # medication was stopped — MUST NOT be treated as current
    RESOLVED = "resolved"          # condition is in the past / cured
    CORRECTED = "corrected"        # was recorded in error, later fixed

    @property
    def is_stale(self) -> bool:
        return self is not ClinicalStatus.ACTIVE


class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life-threatening"


class Medication(BaseModel):
    id: str
    name: str                      # generic name, e.g. "phenelzine"
    drug_class: str | None = None  # e.g. "MAOI" — used by the interaction checker
    dose: str | None = None
    status: ClinicalStatus = ClinicalStatus.ACTIVE
    started: str | None = None     # ISO date
    stopped: str | None = None     # ISO date (set when discontinued)
    reason: str | None = None      # why prescribed / why stopped
    source: str                    # provenance: which document


class Condition(BaseModel):
    id: str
    name: str
    status: ClinicalStatus = ClinicalStatus.ACTIVE
    onset: str | None = None
    resolved: str | None = None
    source: str


class Allergy(BaseModel):
    id: str
    substance: str
    reaction: str | None = None
    severity: Severity = Severity.MODERATE
    source: str


class AdverseReaction(BaseModel):
    """A patient-reported bad reaction — learned over time via improve()."""
    id: str
    drug: str
    reaction: str
    reported: str | None = None
    source: str = "patient-reported"


class Encounter(BaseModel):
    id: str
    date: str
    provider: str | None = None
    specialty: str | None = None
    summary: str | None = None
    source: str


class LabResult(BaseModel):
    id: str
    name: str
    value: str
    unit: str | None = None
    date: str | None = None
    flag: str | None = None        # e.g. "HIGH", "LOW", "CRITICAL"
    source: str


# Any clinical node Aegis can remember/recall/forget.
ClinicalNode = Medication | Condition | Allergy | AdverseReaction | Encounter | LabResult
