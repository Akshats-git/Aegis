"""Ingest the sample patient's structured records into an Aegis memory backend."""

from __future__ import annotations

from .memory import AegisMemory
from .sample_patient import records


def ingest_records(mem: AegisMemory) -> int:
    """Load the structured clinical facts. Returns the number of facts ingested."""
    nodes = records()
    for node in nodes:
        mem.remember(node)
    return len(nodes)
