"""Aegis: a self-correcting clinical memory for patient records.

Aegis maintains a knowledge graph of a patient's history across providers. It retires
stale or superseded facts and checks proposed medications against the current record for
dangerous interactions. It is built on the open-source Cognee library.
"""

from .schema import (
    ClinicalStatus,
    Severity,
    Medication,
    Condition,
    Allergy,
    AdverseReaction,
    Encounter,
    LabResult,
    ClinicalNode,
)
from .memory import AegisMemory, MockMemory, CogneeMemory, get_memory, describe

__all__ = [
    "ClinicalStatus", "Severity", "Medication", "Condition", "Allergy",
    "AdverseReaction", "Encounter", "LabResult", "ClinicalNode",
    "AegisMemory", "MockMemory", "CogneeMemory", "get_memory", "describe",
]
