"""Ingest a patient's fragmented records into the Aegis clinical graph.

Two levels:
  * ingest_records(mem)      — load the structured clinical facts (used everywhere).
  * ingest_raw_notes(mem)    — additionally feed the raw note text to Cognee so it extracts
                               entities itself (shows real ingestion of messy documents).
"""

from __future__ import annotations

from pathlib import Path

from .memory import AegisMemory
from .sample_patient import records

RECORDS_DIR = Path(__file__).resolve().parent.parent / "data" / "records"


def ingest_records(mem: AegisMemory) -> int:
    """Load the structured clinical facts. Returns the number of facts ingested."""
    nodes = records()
    for node in nodes:
        mem.remember(node)
    return len(nodes)


def ingest_raw_notes(mem: AegisMemory) -> int:
    """Feed raw note text to the backend (Cognee will extract from it). Returns file count."""
    files = sorted(RECORDS_DIR.glob("*.md"))
    for f in files:
        # remember() accepts free text; the mock backend simply ignores unstructured input.
        remember_text = getattr(mem, "remember_text", None)
        if callable(remember_text):
            remember_text(f.read_text(), source=f.name)
    return len(files)


def list_record_files() -> list[str]:
    return [f.name for f in sorted(RECORDS_DIR.glob("*.md"))]
