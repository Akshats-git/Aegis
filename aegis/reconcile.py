"""Reconciliation & forget engine.

Fragmented records disagree: the same drug shows up as 'active' in an old list and
'discontinued' in a newer note. A filing cabinet keeps both and lets a human guess. Aegis
decides which fact is authoritative (the most recent record wins) and **forgets the stale
one**, so the current picture a doctor sees is clean and correct.

This is the safety-critical use of forget(): a stale 'active' medication that lingers is
exactly what leads to a wrong, dangerous decision downstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .memory import AegisMemory
from .schema import ClinicalNode, Medication, Condition, ClinicalStatus

_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _source_date(source: str) -> str:
    """Extract an ISO date from a source label for recency comparison ('' if none)."""
    m = _DATE.search(source or "")
    return m.group(0) if m else ""


def _entity_key(node: ClinicalNode) -> tuple[str, str] | None:
    """Group key for facts that describe the same real-world thing."""
    if isinstance(node, Medication):
        return ("medication", node.name.lower())
    if isinstance(node, Condition):
        return ("condition", node.name.lower())
    return None


@dataclass
class ReconcileAction:
    entity: str
    kept_id: str
    kept_status: str
    kept_source: str
    forgotten: list[tuple[str, str, str]] = field(default_factory=list)  # (id, status, source)
    reason: str = ""


def reconcile(nodes: list[ClinicalNode], mem: AegisMemory) -> tuple[list[ReconcileAction], list[ClinicalNode]]:
    """Resolve conflicts and forget() stale facts.

    Returns (actions, clean_nodes) where clean_nodes has the stale duplicates removed.
    """
    groups: dict[tuple[str, str], list[ClinicalNode]] = {}
    for node in nodes:
        key = _entity_key(node)
        if key is not None:
            groups.setdefault(key, []).append(node)

    actions: list[ReconcileAction] = []
    forgotten_ids: set[str] = set()

    for (kind, name), members in groups.items():
        if len(members) < 2:
            continue
        statuses = {getattr(m, "status", ClinicalStatus.ACTIVE) for m in members}
        if len(statuses) < 2:
            continue  # no conflict — same status everywhere

        # Most recent record is authoritative.
        authoritative = max(members, key=lambda m: _source_date(m.source))
        stale = [m for m in members if m.id != authoritative.id]

        for m in stale:
            mem.forget(m.id)
            forgotten_ids.add(m.id)

        actions.append(ReconcileAction(
            entity=name,
            kept_id=authoritative.id,
            kept_status=authoritative.status.value,
            kept_source=authoritative.source,
            forgotten=[(m.id, m.status.value, m.source) for m in stale],
            reason=(f"conflicting {kind} status across records; kept the most recent "
                    f"({_source_date(authoritative.source) or 'undated'})"),
        ))

    clean_nodes = [n for n in nodes if n.id not in forgotten_ids]
    return actions, clean_nodes


def current_medications(nodes: list[ClinicalNode]) -> list[Medication]:
    """The active-medication list after reconciliation — what a safety check must run on."""
    return [n for n in nodes
            if isinstance(n, Medication) and n.status == ClinicalStatus.ACTIVE]
