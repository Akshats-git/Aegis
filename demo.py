"""Phase 1 smoke demo: prove the clinical model + memory engine work (offline, no keys).

    python demo.py

The full lethal-interaction story arrives in later phases. This just shows a few clinical
facts going in, and Aegis surfacing only what is currently TRUE (stale facts excluded).
"""

from __future__ import annotations

from aegis import get_memory, Medication, Condition, ClinicalStatus


def main() -> None:
    mem = get_memory()

    mem.remember(Medication(
        id="med-phenelzine", name="phenelzine", drug_class="MAOI", dose="15mg",
        status=ClinicalStatus.DISCONTINUED, started="2021-03-01", stopped="2023-06-01",
        reason="depression; stopped due to side effects", source="Psychiatry note 2023-06-01",
    ))
    mem.remember(Medication(
        id="med-metoprolol", name="metoprolol", drug_class="beta-blocker", dose="50mg",
        status=ClinicalStatus.ACTIVE, started="2023-04-11",
        reason="hypertension", source="Cardiology consult 2023-04-11",
    ))
    mem.remember(Condition(
        id="cond-htn", name="hypertension", status=ClinicalStatus.ACTIVE,
        onset="2023-04-11", source="Cardiology consult 2023-04-11",
    ))

    print("All facts on record:")
    for n in mem.all_nodes():
        print(f"  - {type(n).__name__}: {getattr(n, 'name', '?')} [{n.status.value}]")

    print("\nWhat Aegis treats as CURRENTLY TRUE (stale facts excluded):")
    for n in mem.active():
        print(f"  - {type(n).__name__}: {getattr(n, 'name', '?')}")

    print("\nNote: the discontinued MAOI is on record but NOT current — "
          "in later phases, forgetting it is what prevents a fatal interaction.")


if __name__ == "__main__":
    main()
