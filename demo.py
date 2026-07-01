"""Phase 3 demo: reconcile the fragmented records and forget the stale facts (offline).

    python demo.py

Shows the current-medication picture BEFORE reconciliation (polluted with a stale
'active' sertraline) and AFTER (Aegis has forgotten it). A clean current picture is the
foundation the Phase 4 safety net depends on.
"""

from __future__ import annotations

from aegis import get_memory, Medication, ClinicalStatus
from aegis.ingest import ingest_records
from aegis.reconcile import reconcile, current_medications
from aegis.sample_patient import records, PROPOSED_DRUG


def _print_meds(nodes) -> None:
    meds = [n for n in nodes if isinstance(n, Medication) and n.status == ClinicalStatus.ACTIVE]
    for m in meds:
        print(f"    - {m.name} [{m.drug_class}]  (per {m.source})")


def main() -> None:
    mem = get_memory()
    nodes = records()
    ingest_records(mem)

    print("Current medications BEFORE reconciliation (what a naive record shows):")
    _print_meds(nodes)

    actions, clean = reconcile(nodes, mem)

    print("\nforget(): Aegis reconciled conflicting records —")
    for a in actions:
        for fid, fstatus, fsrc in a.forgotten:
            print(f"    ✗ forgot '{a.entity}' [{fstatus}] from {fsrc}")
            print(f"      kept the newer fact: [{a.kept_status}] from {a.kept_source}")

    print("\nCurrent medications AFTER reconciliation (clean, trustworthy):")
    _print_meds(clean)

    print("\nWhy it matters:")
    print(f"  The safety net (Phase 4) will check {PROPOSED_DRUG['name']} against THIS clean")
    print("  list. If the stale SSRI had lingered, the interaction picture would be wrong.")
    print("  The active MAOI (phenelzine) correctly remains — and it's the hidden danger.")


if __name__ == "__main__":
    main()
