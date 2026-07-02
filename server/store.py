"""In-memory patient state for the web app.

Holds the current set of clinical facts and source documents. Starts seeded with the demo
patient (so the story is there out of the box), but users can add their own records:

  * add_from_text(): paste a clinical note -> an LLM extracts structured facts.
  * add_manual():    add a single medication/condition/allergy via a form.
  * reset()/clear(): back to the demo, or empty.

This is a single shared store (fine for a demo). The safety pipeline reads from here, so
anything a user adds immediately flows through reconciliation and the interaction checks.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from aegis.schema import (
    Medication, Condition, Allergy, ClinicalStatus, Severity, ClinicalNode,
)
from aegis.sample_patient import records
from aegis.ingest import RECORDS_DIR


def _demo_documents() -> list[dict]:
    return [{"name": f.name, "text": f.read_text()} for f in sorted(RECORDS_DIR.glob("*.md"))]


class PatientStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.facts: list[ClinicalNode] = list(records())
        self.documents: list[dict] = _demo_documents()

    def clear(self) -> None:
        self.facts = []
        self.documents = []

    def all_facts(self) -> list[ClinicalNode]:
        return self.facts

    def add_fact(self, node: ClinicalNode) -> None:
        self.facts.append(node)

    def add_document(self, name: str, text: str) -> None:
        self.documents.append({"name": name, "text": text})

    # ---- structured (form) add ----
    def add_manual(self, kind: str, data: dict) -> ClinicalNode:
        nid = f"user-{kind}-{uuid.uuid4().hex[:8]}"
        source = data.get("source") or "Manually added"
        if kind == "medication":
            node: ClinicalNode = Medication(
                id=nid, name=data["name"], drug_class=data.get("drug_class"),
                dose=data.get("dose"),
                status=ClinicalStatus(data.get("status", "active")),
                started=data.get("started"), stopped=data.get("stopped"),
                reason=data.get("reason"), source=source,
            )
        elif kind == "condition":
            node = Condition(
                id=nid, name=data["name"],
                status=ClinicalStatus(data.get("status", "active")),
                onset=data.get("onset"), resolved=data.get("resolved"), source=source,
            )
        elif kind == "allergy":
            node = Allergy(
                id=nid, substance=data["substance"], reaction=data.get("reaction"),
                severity=Severity(data.get("severity", "moderate")), source=source,
            )
        else:
            raise ValueError(f"unknown kind: {kind}")
        self.add_fact(node)
        return node

    # ---- free-text extraction ----
    def add_from_text(self, text: str, source: str | None = None) -> list[ClinicalNode]:
        source = source or "Uploaded note"
        extracted = extract_facts(text, source)
        for node in extracted:
            self.add_fact(node)
        self.add_document(source, text)
        return extracted


store = PatientStore()


# Drug classes the interaction checker understands (steer the LLM toward these).
KNOWN_CLASSES = [
    "MAOI", "SSRI", "SNRI", "triptan", "beta-blocker", "NSAID", "opioid",
    "sympathomimetic", "antitussive", "anticoagulant", "ACE inhibitor",
    "potassium-sparing diuretic", "analgesic",
]

_SCHEMA_HINT = f"""Return ONLY JSON with this shape:
{{
  "medications": [{{"name": str, "drug_class": str, "dose": str|null,
                    "status": "active"|"discontinued", "started": str|null,
                    "stopped": str|null, "reason": str|null}}],
  "conditions":  [{{"name": str, "status": "active"|"resolved", "onset": str|null}}],
  "allergies":   [{{"substance": str, "reaction": str|null,
                    "severity": "mild"|"moderate"|"severe"|"life-threatening"}}]
}}
For drug_class, prefer one of: {", ".join(KNOWN_CLASSES)} (use the closest match).
Use ISO dates (YYYY-MM-DD) when present. Omit fields you cannot find (use null)."""


def extract_facts(text: str, source: str) -> list[ClinicalNode]:
    """Use an LLM to turn a free-text clinical note into structured facts."""
    from openai import OpenAI

    key = os.getenv("LLM_API_KEY")
    if not key:
        raise RuntimeError("LLM_API_KEY not set — cannot extract from text.")
    client = OpenAI(api_key=key)
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role": "system",
             "content": "You extract structured clinical facts from medical notes. "
                        + _SCHEMA_HINT},
            {"role": "user", "content": text},
        ],
    )
    data = json.loads(resp.choices[0].message.content or "{}")

    out: list[ClinicalNode] = []
    for m in data.get("medications", []):
        if not m.get("name"):
            continue
        out.append(Medication(
            id=f"user-med-{uuid.uuid4().hex[:8]}", name=m["name"],
            drug_class=m.get("drug_class"), dose=m.get("dose"),
            status=_status(m.get("status"), ClinicalStatus.ACTIVE),
            started=m.get("started"), stopped=m.get("stopped"),
            reason=m.get("reason"), source=source,
        ))
    for c in data.get("conditions", []):
        if not c.get("name"):
            continue
        out.append(Condition(
            id=f"user-cond-{uuid.uuid4().hex[:8]}", name=c["name"],
            status=_status(c.get("status"), ClinicalStatus.ACTIVE),
            onset=c.get("onset"), source=source,
        ))
    for a in data.get("allergies", []):
        if not a.get("substance"):
            continue
        out.append(Allergy(
            id=f"user-allergy-{uuid.uuid4().hex[:8]}", substance=a["substance"],
            reaction=a.get("reaction"),
            severity=_severity(a.get("severity")), source=source,
        ))
    return out


def _status(v, default: ClinicalStatus) -> ClinicalStatus:
    try:
        return ClinicalStatus(v)
    except (ValueError, TypeError):
        return default


def _severity(v) -> Severity:
    try:
        return Severity(v)
    except (ValueError, TypeError):
        return Severity.MODERATE
