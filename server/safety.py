"""Medication safety assessment for a clinician.

Given a proposed medicine (typed by name) and the patient's reconciled current record, this
combines two layers:

  1. Deterministic rules (aegis/interactions.py) cover the known, high-stakes
     contraindications. They are always caught, high confidence, and labelled "reference".
     The AI layer never overrides them.
  2. A broad AI assessment covers the long tail. It is labelled "cognee" when it comes from
     the patient's own Cognee memory graph, which is graph-grounded and cited through the
     same recall() pipeline "Ask Aegis" uses. It is labelled "ai" when Cognee is unavailable
     and the code falls back to a direct LLM call over the reconciled context.

Built for the emergency case: a doctor is handed the patient's record and needs to know
quickly whether a new medicine is safe given everything on file.
"""

from __future__ import annotations

import json
import os

from aegis.memory import MockMemory
from aegis.reconcile import reconcile, current_medications
from aegis.interactions import check, suggest_alternatives
from aegis.schema import Condition, Allergy, ClinicalStatus

SEV_ORDER = {"life-threatening": 0, "severe": 1, "moderate": 2, "mild": 3}


def _reconciled_context(store):
    mem = MockMemory()
    nodes = store.all_facts()
    for n in nodes:
        mem.remember(n)
    _, clean = reconcile(nodes, mem)
    meds = current_medications(clean)
    conditions = [n.name for n in clean
                  if isinstance(n, Condition) and n.status == ClinicalStatus.ACTIVE]
    allergies = [n for n in clean if isinstance(n, Allergy)]
    return meds, conditions, allergies


def _ai_assess(name, meds, conditions, allergies, indication=None) -> tuple[dict, bool]:
    """Broad AI safety assessment. Tries Cognee's graph-grounded, cited recall first (the
    same memory "Ask Aegis" answers from), then falls back to a direct LLM call with the
    reconciled context if Cognee is unavailable or its answer is not usable JSON. Returns
    (result, from_cognee)."""
    from server import cognee_bridge

    got = cognee_bridge.assess(name, indication)
    if got is not None:
        return got, True

    key = os.getenv("LLM_API_KEY")
    if not key:
        return {"drug_class": "", "concerns": [], "safe_alternatives": []}, False
    from openai import OpenAI

    client = OpenAI(api_key=key)
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    med_list = "; ".join(f"{m.name} ({m.drug_class or 'unclassified'})" for m in meds) or "none"
    cond_list = ", ".join(conditions) or "none"
    alg_list = ", ".join(a.substance for a in allergies) or "none"

    from server.store import KNOWN_CLASSES

    system = (
        "You are a clinical medication-safety assistant supporting a doctor making an "
        "urgent treatment decision. Given a proposed new medicine and the patient's current "
        "medications, active conditions and allergies, assess whether it is safe. Identify "
        "clinically significant drug-drug interactions, drug-condition contraindications, and "
        "allergy risks. For drug_class, prefer one of these exact labels when applicable: "
        f"{', '.join(KNOWN_CLASSES)}. Return ONLY JSON of the form: {{\"drug_class\": string, \"concerns\": "
        "[{\"severity\": \"life-threatening\"|\"severe\"|\"moderate\"|\"mild\", \"concern\": "
        "short title, \"reason\": one plain-English sentence, \"related_to\": the specific "
        "current medicine, condition or allergy it relates to}], \"safe_alternatives\": "
        "[string]}. List only real, clinically significant concerns; if there are none, "
        "return an empty concerns list. Be conservative and accurate: only report "
        "interactions that are well-established and clinically significant in standard "
        "references. Do NOT report theoretical, speculative or minor concerns. Common "
        "analgesics such as acetaminophen (paracetamol) are not serotonergic and are "
        "considered safe with MAOIs, so do not flag them for serotonin syndrome. If the "
        "medicine is a standard, safe choice for this patient, return no concerns."
    )
    user = (
        f"Proposed new medicine: {name}\n"
        f"Current medications: {med_list}\n"
        f"Active conditions: {cond_list}\n"
        f"Known allergies: {alg_list}"
    )
    try:
        resp = client.chat.completions.create(
            model=model, temperature=0, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return json.loads(resp.choices[0].message.content or "{}"), False
    except Exception:
        return {"drug_class": "", "concerns": [], "safe_alternatives": []}, False


def assess(store, name: str, indication: str | None = None) -> dict:
    name = (name or "").strip()
    meds, conditions, allergies = _reconciled_context(store)

    ai, from_cognee = _ai_assess(name, meds, conditions, allergies, indication)
    drug_class = (ai.get("drug_class") or "").strip()
    ai_source = "cognee" if from_cognee else "ai"
    grounded_evidence = (ai.get("_evidence") or []) if from_cognee else []

    concerns: list[dict] = []

    # 1) deterministic, authoritative rules
    det = check(name, drug_class, meds, allergies)
    det_tokens = set()
    for a in det:
        first = a.conflicting_drug.split(" ")[0].lower()
        det_tokens.add(first)
        concerns.append({
            "severity": a.severity.value,
            "title": a.effect,
            "detail": a.management,
            "related_to": a.conflicting_drug,
            "source": "reference",
        })

    # 2) AI concerns (skip ones already covered by a deterministic rule for the same drug)
    for c in ai.get("concerns", []) or []:
        rel = str(c.get("related_to", "")).lower()
        if any(tok and tok in rel for tok in det_tokens):
            continue
        sev = c.get("severity", "moderate")
        if sev not in SEV_ORDER:
            sev = "moderate"
        title = str(c.get("concern", "")).strip()
        if not title:
            continue
        concerns.append({
            "severity": sev,
            "title": title,
            "detail": str(c.get("reason", "")).strip(),
            "related_to": str(c.get("related_to", "")).strip(),
            "source": ai_source,
        })

    concerns.sort(key=lambda c: SEV_ORDER.get(c["severity"], 3))

    # Only the deterministic rules can block. AI concerns are advisory and cap the verdict
    # at "caution", so an AI false positive can never block a medicine that is actually safe.
    ref_block = any(c["source"] == "reference" and SEV_ORDER.get(c["severity"], 3) <= 1
                    for c in concerns)
    if ref_block:
        verdict = "block"
    elif concerns:
        verdict = "caution"
    else:
        verdict = "ok"

    alternatives: list[str] = []
    if verdict != "ok":
        alternatives = ai.get("safe_alternatives") or suggest_alternatives(indication or "")

    return {
        "proposed": {"name": name, "drug_class": drug_class},
        "verdict": verdict,
        "concerns": concerns,
        "alternatives": alternatives,
        "grounded_evidence": grounded_evidence,
        "checked_against": {
            "medications": len(meds),
            "conditions": len(conditions),
            "allergies": len(allergies),
        },
    }
