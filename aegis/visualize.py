"""Terminal visualization: a medication timeline and a safety card.

    python -m aegis.visualize

Uses only the standard library (ANSI colors) so it renders anywhere. Runs the offline
pipeline, so it needs no API keys.
"""

from __future__ import annotations

from aegis import get_memory, Medication, Condition, Allergy, ClinicalStatus
from aegis.ingest import ingest_records
from aegis.reconcile import reconcile, current_medications
from aegis.interactions import check, suggest_alternatives
from aegis.sample_patient import records, PROPOSED_DRUG

R = "\033[31m"; G = "\033[32m"; Y = "\033[33m"; DIM = "\033[2m"; B = "\033[1m"; X = "\033[0m"


def timeline(nodes) -> None:
    print(f"{B}  MEDICATION TIMELINE{X}\n")
    meds = [n for n in nodes if isinstance(n, Medication)]
    meds.sort(key=lambda m: m.started or "")
    for m in meds:
        if m.status == ClinicalStatus.ACTIVE:
            bar, tag = f"{G}", f"{G}● active{X}"
        else:
            bar, tag = f"{DIM}", f"{DIM}○ {m.status.value}{X}"
        span = f"{m.started or '?'} → {m.stopped or 'present'}"
        danger = f"  {R}{B}⚠ MAOI{X}" if (m.drug_class == "MAOI" and m.status == ClinicalStatus.ACTIVE) else ""
        print(f"  {bar}{m.name:<12}{X} {DIM}[{m.drug_class}]{X}  {span:<24} {tag}{danger}")
    print()


def safety_card(proposed, alerts) -> None:
    width = 66
    if any(a.is_blocking for a in alerts):
        a = alerts[0]
        print(f"{R}{B}  ┏{'━' * width}┓{X}")
        print(f"{R}{B}  ┃  🚨  DO NOT PRESCRIBE: {proposed['name'].upper():<38}┃{X}")
        print(f"{R}{B}  ┗{'━' * width}┛{X}")
        print(f"     {R}{a.severity.value.upper()}: {a.effect}{X}")
        print(f"     {a.proposed_drug} ✕ {a.conflicting_drug}")
        print(f"     {DIM}why: {a.mechanism}{X}")
        print(f"     {DIM}evidence: {a.patient_source} · {a.evidence_source}{X}")
        print(f"\n  {G}{B}  ✓ Safer alternatives:{X}")
        for alt in suggest_alternatives("migraine"):
            print(f"     {G}• {alt}{X}")
    else:
        print(f"{G}{B}  ✓ {proposed['name']} appears safe against the current record.{X}")
    print()


def main() -> None:
    mem = get_memory()
    nodes = records()
    ingest_records(mem)
    _, clean = reconcile(nodes, mem)

    print(f"\n{B}══ AEGIS · patient safety view ═════════════════════════════════════{X}\n")
    timeline(clean)
    print(f"{B}  PROPOSED TODAY:{X} {PROPOSED_DRUG['name']} ({PROPOSED_DRUG['drug_class']}) for acute migraine\n")
    alerts = check(PROPOSED_DRUG["name"], PROPOSED_DRUG["drug_class"], current_medications(clean))
    safety_card(PROPOSED_DRUG, alerts)


if __name__ == "__main__":
    main()
