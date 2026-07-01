"""Turn raw ADRs / PR notes / changelogs into Canon graph nodes.

For the hackathon, the LLM-normalization step (messy release notes -> structured nodes)
is a legit use of an AI assistant. Here we ingest the structured sample data directly;
swap `parse_*` for an LLM pass over real text when you wire the Cognee backend.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schema import Decision, Symbol
from .memory import CanonMemory

DATA = Path(__file__).resolve().parent.parent / "data"


def load_decisions() -> list[Decision]:
    return [Decision(**d) for d in json.loads((DATA / "decisions.json").read_text())]


def load_symbols() -> list[Symbol]:
    return [Symbol(**s) for s in json.loads((DATA / "symbols.json").read_text())]


def ingest_all(mem: CanonMemory) -> None:
    for node in (*load_decisions(), *load_symbols()):
        mem.remember(node)
