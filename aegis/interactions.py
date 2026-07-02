"""Drug-interaction safety net.

A curated, open knowledge base of clinically significant drug-drug interactions, keyed by
drug class (more robust than exact drug names). Facts here are well-established
contraindications from public sources (FDA prescribing information / DailyMed, NIH RxNav /
openFDA) — the same open data an unlimited version would pull live.

check() takes the patient's CLEAN current medication list (post-reconciliation) plus a
proposed new drug, and returns safety alerts, each citing BOTH the patient's source note
and the interaction reference. That provenance is what makes a warning trustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Medication, Allergy, Severity

FDA = "FDA prescribing information (DailyMed / openFDA)"


@dataclass(frozen=True)
class Interaction:
    class_a: str
    class_b: str
    severity: Severity
    effect: str
    mechanism: str
    management: str
    source: str = FDA

    def matches(self, ca: str, cb: str) -> bool:
        pair = {self.class_a.lower(), self.class_b.lower()}
        return pair == {ca.lower(), cb.lower()}


# --- Open interaction knowledge base (class-level) ---
INTERACTIONS: list[Interaction] = [
    Interaction("MAOI", "triptan", Severity.LIFE_THREATENING,
                "serotonin syndrome",
                "additive serotonergic activity (5-HT)",
                "CONTRAINDICATED. Do not co-administer. Avoid triptans while on an MAOI "
                "and for 2 weeks after stopping it."),
    Interaction("MAOI", "SSRI", Severity.LIFE_THREATENING,
                "serotonin syndrome",
                "additive serotonergic activity; MAO inhibition raises serotonin",
                "CONTRAINDICATED. Requires a 14-day washout between an MAOI and an SSRI."),
    Interaction("MAOI", "SNRI", Severity.LIFE_THREATENING,
                "serotonin syndrome",
                "additive serotonergic activity",
                "CONTRAINDICATED. 14-day washout required."),
    Interaction("MAOI", "opioid", Severity.LIFE_THREATENING,
                "serotonin syndrome / severe reactions (esp. meperidine, tramadol)",
                "serotonergic and CNS effects",
                "Avoid meperidine and tramadol with MAOIs. Use non-serotonergic analgesia."),
    Interaction("MAOI", "sympathomimetic", Severity.LIFE_THREATENING,
                "hypertensive crisis",
                "blocked catecholamine metabolism → surge in blood pressure",
                "CONTRAINDICATED. Avoid decongestants/stimulants with MAOIs."),
    Interaction("MAOI", "antitussive", Severity.SEVERE,
                "serotonin syndrome (dextromethorphan)",
                "serotonergic activity",
                "Avoid dextromethorphan-containing products with MAOIs."),
    # A few beyond the demo, to show the checker generalizes:
    Interaction("anticoagulant", "NSAID", Severity.SEVERE,
                "increased bleeding risk",
                "additive effects on hemostasis + GI irritation",
                "Avoid combination; if needed, use gastroprotection and monitor closely."),
    Interaction("ACE inhibitor", "potassium-sparing diuretic", Severity.MODERATE,
                "hyperkalemia",
                "additive potassium retention",
                "Monitor serum potassium; avoid in renal impairment."),
]


@dataclass
class SafetyAlert:
    severity: Severity
    proposed_drug: str
    conflicting_drug: str
    effect: str
    mechanism: str
    management: str
    patient_source: str        # which note the conflicting current med came from
    evidence_source: str       # the interaction reference

    @property
    def is_blocking(self) -> bool:
        return self.severity in (Severity.SEVERE, Severity.LIFE_THREATENING)


def _find(class_a: str, class_b: str) -> Interaction | None:
    if not class_a or not class_b:
        return None
    for ix in INTERACTIONS:
        if ix.matches(class_a, class_b):
            return ix
    return None


def check(proposed_name: str, proposed_class: str,
          current_meds: list[Medication],
          allergies: list[Allergy] | None = None) -> list[SafetyAlert]:
    """Check a proposed drug against the patient's clean current picture."""
    alerts: list[SafetyAlert] = []

    for med in current_meds:
        ix = _find(proposed_class, med.drug_class or "")
        if ix:
            alerts.append(SafetyAlert(
                severity=ix.severity,
                proposed_drug=proposed_name,
                conflicting_drug=f"{med.name} ({med.drug_class})",
                effect=ix.effect,
                mechanism=ix.mechanism,
                management=ix.management,
                patient_source=med.source,
                evidence_source=ix.source,
            ))

    for allergy in (allergies or []):
        if allergy.substance.lower() in proposed_name.lower():
            alerts.append(SafetyAlert(
                severity=Severity.SEVERE,
                proposed_drug=proposed_name,
                conflicting_drug=f"documented allergy: {allergy.substance}",
                effect=allergy.reaction or "allergic reaction",
                mechanism="known hypersensitivity",
                management="Avoid. Select an agent from a different class.",
                patient_source=allergy.source,
                evidence_source="patient allergy record",
            ))

    # worst first
    order = {Severity.LIFE_THREATENING: 0, Severity.SEVERE: 1,
             Severity.MODERATE: 2, Severity.MILD: 3}
    alerts.sort(key=lambda a: order[a.severity])
    return alerts


# Safe alternatives by indication when the first choice is blocked (conservative, generic).
SAFE_ALTERNATIVES = {
    "migraine": ["acetaminophen (paracetamol)",
                 "an antiemetic such as metoclopramide for nausea",
                 "non-drug measures (dark room, hydration)"],
}


def suggest_alternatives(indication: str) -> list[str]:
    return SAFE_ALTERNATIVES.get(indication.lower(), [])


# Drugs a clinician might propose in the UI — chosen to show a range of outcomes against
# this patient (some catch the MAOI danger, some are safe).
CANDIDATE_DRUGS = [
    {"name": "sumatriptan", "drug_class": "triptan", "indication": "migraine"},
    {"name": "dextromethorphan", "drug_class": "antitussive", "indication": "cough"},
    {"name": "pseudoephedrine", "drug_class": "sympathomimetic", "indication": "congestion"},
    {"name": "ibuprofen", "drug_class": "NSAID", "indication": "pain"},
    {"name": "acetaminophen", "drug_class": "analgesic", "indication": "migraine"},
]
