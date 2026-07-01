"""Aegis — the memory that keeps your health record honest.

A living, self-correcting clinical knowledge graph that remembers a patient's full history
across every provider, retires stale/dangerous facts (forget), and acts as a safety net
against dangerous drug interactions. Built on open-source Cognee.
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
