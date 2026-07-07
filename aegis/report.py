"""The new-provider handoff view.

When a patient sees a provider who has never treated them, Aegis produces an accurate,
current summary. It is built from the reconciled facts, so it excludes stale entries but
still flags recently discontinued drugs that matter, such as an MAOI washout window.
"""

from __future__ import annotations

from .schema import (
    ClinicalNode, Medication, Condition, Allergy, ClinicalStatus,
)


def handoff_summary(nodes: list[ClinicalNode]) -> str:
    conditions = [n for n in nodes if isinstance(n, Condition) and n.status == ClinicalStatus.ACTIVE]
    current_meds = [n for n in nodes if isinstance(n, Medication) and n.status == ClinicalStatus.ACTIVE]
    stopped_meds = [n for n in nodes if isinstance(n, Medication) and n.status == ClinicalStatus.DISCONTINUED]
    allergies = [n for n in nodes if isinstance(n, Allergy)]

    lines: list[str] = ["PATIENT HANDOFF SUMMARY (current, reconciled)"]

    lines.append("\nActive conditions:")
    lines += [f"  - {c.name}" for c in conditions] or ["  - none on record"]

    lines.append("\nCurrent medications:")
    lines += [f"  - {m.name} {m.dose or ''} [{m.drug_class}]".rstrip()
              for m in current_meds] or ["  - none on record"]

    lines.append("\nDocumented allergies:")
    lines += [f"  - {a.substance} ({a.reaction})" for a in allergies] or ["  - none on record"]

    if stopped_meds:
        lines.append("\nRecently discontinued (still relevant for interactions/washout):")
        lines += [f"  - {m.name}, stopped {m.stopped or 'date unknown'}" for m in stopped_meds]

    return "\n".join(lines)
