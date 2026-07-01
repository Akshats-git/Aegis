"""The demo patient (synthetic): Margaret Chen.

These are the clinical facts as they appear across four fragmented source documents in
data/records/. Note the deliberately conflicting facts about sertraline — one source
(older PCP list) still shows it ACTIVE, while psychiatry later DISCONTINUED it. That
fragmentation is exactly what gets real patients hurt, and what Aegis reconciles.

The planted danger:
  * phenelzine (an MAOI) is CURRENTLY ACTIVE but buried in a psychiatry note.
  * today an urgent-care doctor, without those records, is about to give sumatriptan
    (a triptan) for a migraine — contraindicated with an MAOI (serotonin syndrome).
"""

from __future__ import annotations

from .schema import (
    Medication, Condition, Allergy, Encounter, ClinicalStatus, Severity, ClinicalNode,
)

PCP_LIST = "PCP medication list (2023-05-02)"
CARDIO = "Cardiology consult (2023-04-11)"
PSYCH = "Psychiatry note (2024-01-15)"
URGENT = "Urgent care visit (2026-07-02)"


def records() -> list[ClinicalNode]:
    return [
        # --- Conditions ---
        Condition(id="cond-htn", name="essential hypertension",
                  status=ClinicalStatus.ACTIVE, onset="2023-04-11", source=CARDIO),
        Condition(id="cond-mdd", name="major depressive disorder (treatment-resistant)",
                  status=ClinicalStatus.ACTIVE, onset="2021", source=PSYCH),
        Condition(id="cond-migraine", name="acute migraine",
                  status=ClinicalStatus.ACTIVE, onset="2026-07-02", source=URGENT),

        # --- Medications ---
        Medication(id="med-metoprolol", name="metoprolol", drug_class="beta-blocker",
                   dose="50mg daily", status=ClinicalStatus.ACTIVE, started="2023-04-11",
                   reason="hypertension", source=CARDIO),

        # CONFLICT: the PCP list (older) still shows sertraline as an ACTIVE medication...
        Medication(id="med-sertraline-pcp", name="sertraline", drug_class="SSRI",
                   dose="100mg daily", status=ClinicalStatus.ACTIVE, started="2021",
                   reason="depression", source=PCP_LIST),

        # ...but psychiatry later DISCONTINUED it (the correct, more recent fact).
        Medication(id="med-sertraline-psych", name="sertraline", drug_class="SSRI",
                   dose="100mg daily", status=ClinicalStatus.DISCONTINUED, started="2021",
                   stopped="2024-01-08", reason="inadequate response; switched to MAOI",
                   source=PSYCH),

        # THE BURIED DANGER: an active MAOI.
        Medication(id="med-phenelzine", name="phenelzine", drug_class="MAOI",
                   dose="15mg three times daily", status=ClinicalStatus.ACTIVE,
                   started="2024-01-15", reason="treatment-resistant depression",
                   source=PSYCH),

        # --- Allergy ---
        Allergy(id="allergy-penicillin", substance="penicillin", reaction="hives",
                severity=Severity.MODERATE, source=PCP_LIST),

        # --- Today's encounter (the proposed, dangerous prescription lives here) ---
        Encounter(id="enc-urgent-2026", date="2026-07-02", provider="Dr. J. Whitfield",
                  specialty="Urgent Care",
                  summary="Acute migraine. Considering sumatriptan 50mg (safety check pending).",
                  source=URGENT),
    ]


# The drug the urgent-care doctor is about to prescribe (used by the Phase 4 safety net).
PROPOSED_DRUG = {"name": "sumatriptan", "drug_class": "triptan"}
