"""Phase 4 demo: the full safety story, offline (no keys).

    python demo.py

Naive path: a doctor prescribes sumatriptan for a migraine → serotonin syndrome.
Aegis path: reconcile → forget stale facts → check the clean picture → catch the fatal
MAOI interaction, cite the source note, and suggest a safe alternative.
"""

from __future__ import annotations

from aegis import get_memory, Medication, ClinicalStatus, Allergy
from aegis.ingest import ingest_records
from aegis.reconcile import reconcile, current_medications
from aegis.interactions import check, suggest_alternatives
from aegis.sample_patient import records, PROPOSED_DRUG


def line() -> None:
    print("-" * 68)


def main() -> None:
    mem = get_memory()
    nodes = records()
    ingest_records(mem)

    proposed = PROPOSED_DRUG  # sumatriptan (triptan) for the migraine

    line()
    print("NAIVE PATH — doctor without the full, current picture")
    line()
    print(f"  Prescribes {proposed['name']} for acute migraine.")
    print("  ☠️  Result: co-administered with the patient's active MAOI (phenelzine),")
    print("      this can cause SEROTONIN SYNDROME — potentially fatal.")

    # Aegis path
    actions, clean = reconcile(nodes, mem)
    current = current_medications(clean)
    allergies = [n for n in clean if isinstance(n, Allergy)]
    alerts = check(proposed["name"], proposed["drug_class"], current, allergies)

    print()
    line()
    print("AEGIS PATH — reconcile, forget, then safety-check the clean picture")
    line()
    print("  Current medications (after forgetting stale facts):")
    for m in current:
        print(f"    - {m.name} [{m.drug_class}]  (per {m.source})")

    print(f"\n  Safety check: {proposed['name']} ({proposed['drug_class']})")
    if not alerts:
        print("    ✅ No interactions found.")
    for a in alerts:
        print()
        print(f"    🚨 {a.severity.value.upper()}: risk of {a.effect}")
        print(f"       {a.proposed_drug}  ✕  {a.conflicting_drug}")
        print(f"       Mechanism: {a.mechanism}")
        print(f"       Action: {a.management}")
        print(f"       Evidence: patient fact from '{a.patient_source}'")
        print(f"                 interaction per {a.evidence_source}")

    if any(a.is_blocking for a in alerts):
        alts = suggest_alternatives("migraine")
        print("\n  🟢 Safer alternatives for migraine (discuss with prescriber):")
        for alt in alts:
            print(f"       - {alt}")

    print()
    line()
    print("Aegis caught what a fragmented record would have missed. That's the difference")
    print("between a filing cabinet and a memory that keeps you safe.")


if __name__ == "__main__":
    main()
