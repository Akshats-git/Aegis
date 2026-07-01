"""Phase 2 demo: ingest a patient's fragmented records and expose the danger (offline).

    python demo.py

Loads the synthetic patient (4 source documents) into the health memory and shows the
fragmented, conflicting picture a new doctor would face. Reconciliation (forgetting the
stale facts) and the safety net arrive in the next phases.
"""

from __future__ import annotations

from collections import defaultdict

from aegis import get_memory, Medication
from aegis.ingest import ingest_records, list_record_files
from aegis.sample_patient import PROPOSED_DRUG


def main() -> None:
    mem = get_memory()

    print("Source documents on file (fragmented across clinics):")
    for f in list_record_files():
        print(f"  - {f}")

    n = ingest_records(mem)
    print(f"\nremember(): ingested {n} clinical facts into the graph.\n")

    print("Medications on record, grouped by drug (note the conflict):")
    by_name: dict[str, list[Medication]] = defaultdict(list)
    for node in mem.all_nodes():
        if isinstance(node, Medication):
            by_name[node.name].append(node)
    for name, meds in by_name.items():
        statuses = ", ".join(f"{m.status.value} (per {m.source})" for m in meds)
        flag = "  <-- CONFLICT" if len({m.status for m in meds}) > 1 else ""
        print(f"  - {name}: {statuses}{flag}")

    print("\n⚠️  The danger:")
    print(f"  Today a doctor wants to prescribe {PROPOSED_DRUG['name']} "
          f"({PROPOSED_DRUG['drug_class']}) for a migraine.")
    print("  An active MAOI (phenelzine) is buried in the psychiatry note, and the record")
    print("  still shows a discontinued SSRI as 'active'. Getting this picture right is")
    print("  literally life-or-death — that's what Phase 3 (reconcile/forget) and Phase 4")
    print("  (interaction safety net) do next.")


if __name__ == "__main__":
    main()
