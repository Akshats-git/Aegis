"""Per-user patient state for the web app.

Each signed-in user gets their own profile (an isolated set of clinical facts + source
documents), persisted to disk so it survives restarts. New profiles start EMPTY — there is
no preloaded demo patient.

  * add_from_text(): paste a clinical note -> an LLM extracts structured facts.
  * add_manual():    add a single medication/condition/allergy via a form.
  * clear():         empty the profile.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

from aegis.schema import (
    Medication, Condition, Allergy, ClinicalStatus, Severity, ClinicalNode,
)

DATA_DIR = Path(__file__).resolve().parent / "_userdata"
DATA_DIR.mkdir(exist_ok=True)

_TYPES = {"Medication": Medication, "Condition": Condition, "Allergy": Allergy}


def _encode(node: ClinicalNode) -> dict:
    return {"type": type(node).__name__, "data": node.model_dump(mode="json")}


def _decode(rec: dict) -> ClinicalNode | None:
    cls = _TYPES.get(rec.get("type", ""))
    return cls(**rec["data"]) if cls else None


class PatientStore:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.facts: list[ClinicalNode] = []
        self.documents: list[dict] = []
        self._load()

    # ---- persistence ----
    def _path(self) -> Path:
        key = hashlib.sha256(self.user_id.encode()).hexdigest()[:24]
        return DATA_DIR / f"{key}.json"

    def _load(self) -> None:
        p = self._path()
        if not p.exists():
            return
        try:
            blob = json.loads(p.read_text())
            self.facts = [n for n in (_decode(r) for r in blob.get("facts", [])) if n]
            self.documents = blob.get("documents", [])
        except Exception:
            self.facts, self.documents = [], []

    def _save(self) -> None:
        self._path().write_text(json.dumps({
            "facts": [_encode(n) for n in self.facts],
            "documents": self.documents,
        }, indent=2))

    # ---- state ----
    def all_facts(self) -> list[ClinicalNode]:
        return self.facts

    def add_fact(self, node: ClinicalNode) -> None:
        self.facts.append(node)
        self._save()

    def add_document(self, name: str, text: str) -> None:
        self.documents.append({"name": name, "text": text})
        self._save()

    def clear(self) -> None:
        self.facts = []
        self.documents = []
        self._save()

    # ---- structured (form) add ----
    def add_manual(self, kind: str, data: dict) -> ClinicalNode:
        nid = f"user-{kind}-{uuid.uuid4().hex[:8]}"
        source = data.get("source") or "Added by you"
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
            self.facts.append(node)
        self.documents.append({"name": source, "text": text})
        self._save()
        return extracted


# ---- per-user registry ----
_stores: dict[str, PatientStore] = {}


def get_store(user_id: str) -> PatientStore:
    uid = (user_id or "anonymous").strip() or "anonymous"
    if uid not in _stores:
        _stores[uid] = PatientStore(uid)
    return _stores[uid]


# ---- LLM extraction (shared) ----
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
        raise RuntimeError("Text extraction is not configured on the server.")
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
