"""Aegis API.

    uvicorn server.app:app --reload --port 8000

Each request carries an X-User-Id header (the signed-in user's id, injected by the web app);
the deterministic JSON record (documents/facts) is isolated per user. The Cognee-backed
memory graph (recall, the safety check's AI layer, erase) is single-tenant — one shared
graph for the record currently being managed — by design; see aegis/memory.py.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # make LLM_API_KEY etc. available for text extraction and Cognee

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aegis import Medication, Condition, Allergy, ClinicalStatus
from aegis.sample_patient import PROPOSED_DRUG
from aegis.reconcile import reconcile, current_medications
from aegis.interactions import check, suggest_alternatives, CANDIDATE_DRUGS
from aegis.report import handoff_summary
from aegis.memory import MockMemory
from server.store import get_store, PatientStore
from server import cognee_bridge

app = FastAPI(title="Aegis API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def user_store(x_user_id: str = Header(default="anonymous")) -> PatientStore:
    return get_store(x_user_id)


# ---------- accounts (email + password) ----------

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/register")
def auth_register(req: RegisterRequest):
    from server.auth import get_user_store, AuthError
    try:
        return get_user_store().register(req.email, req.password, req.name)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    from server.auth import get_user_store, AuthError
    try:
        return get_user_store().authenticate(req.email, req.password)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    current_password: str | None = None
    new_password: str | None = None


@app.post("/api/auth/update")
def auth_update(req: UpdateProfileRequest, x_user_id: str = Header(default="")):
    from server.auth import get_user_store, AuthError
    try:
        return get_user_store().update(
            x_user_id, req.name, req.current_password, req.new_password
        )
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _reconciled(store: PatientStore):
    """Return (actions, clean_nodes) over the user's profile (instant)."""
    mem = MockMemory()
    nodes = store.all_facts()
    for n in nodes:
        mem.remember(n)
    return reconcile(nodes, mem), nodes


# ---------- deterministic endpoints (instant) ----------

@app.get("/api/patient")
def get_patient(store: PatientStore = Depends(user_store)):
    return {"documents": store.documents, "has_data": len(store.all_facts()) > 0}


@app.get("/api/timeline")
def get_timeline(store: PatientStore = Depends(user_store)):
    (_, clean), all_nodes = _reconciled(store)
    meds = []
    for n in all_nodes:
        if isinstance(n, Medication):
            meds.append({
                "id": n.id, "name": n.name, "drug_class": n.drug_class,
                "dose": n.dose, "status": n.status.value,
                "started": n.started, "stopped": n.stopped, "source": n.source,
                "forgotten": n.id not in {c.id for c in clean},
                "danger": n.drug_class == "MAOI" and n.status == ClinicalStatus.ACTIVE,
            })
    meds.sort(key=lambda m: m["started"] or "")
    return {"medications": meds}


@app.get("/api/reconcile")
def get_reconcile(store: PatientStore = Depends(user_store)):
    (actions, clean), _ = _reconciled(store)
    return {
        "actions": [{
            "entity": a.entity, "kept_status": a.kept_status, "kept_source": a.kept_source,
            "forgotten": [{"status": s, "source": src} for _, s, src in a.forgotten],
            "reason": a.reason,
        } for a in actions],
        "current_medications": [
            {"name": m.name, "drug_class": m.drug_class, "dose": m.dose, "source": m.source}
            for m in current_medications(clean)
        ],
    }


@app.get("/api/handoff")
def get_handoff(store: PatientStore = Depends(user_store)):
    (_, clean), _ = _reconciled(store)
    conditions = [{"name": n.name, "onset": n.onset}
                  for n in clean if isinstance(n, Condition) and n.status == ClinicalStatus.ACTIVE]
    meds = [{"name": m.name, "dose": m.dose, "drug_class": m.drug_class, "started": m.started}
            for m in current_medications(clean)]
    allergies = [{"substance": a.substance, "reaction": a.reaction, "severity": a.severity.value}
                 for a in clean if isinstance(a, Allergy)]
    discontinued = [{"name": n.name, "stopped": n.stopped, "reason": n.reason}
                    for n in clean if isinstance(n, Medication) and n.status == ClinicalStatus.DISCONTINUED]
    return {"conditions": conditions, "medications": meds, "allergies": allergies,
            "discontinued": discontinued, "text": handoff_summary(clean) if clean else ""}


@app.get("/api/candidates")
def get_candidates():
    return {"candidates": CANDIDATE_DRUGS, "default": PROPOSED_DRUG}


class SafetyRequest(BaseModel):
    name: str
    drug_class: str | None = None
    indication: str | None = None


@app.post("/api/safety-check")
def safety_check(req: SafetyRequest, store: PatientStore = Depends(user_store)):
    from server.safety import assess
    return assess(store, req.name, req.indication)


# ---------- recall / erase ----------

class RecallRequest(BaseModel):
    query: str = "List my current medications and what to avoid taking."


def _cited_from_records(store: PatientStore) -> dict:
    (_, clean), _ = _reconciled(store)
    meds = current_medications(clean)
    if not meds:
        return {"answer": "You haven't added any records yet.", "evidence": [], "engine": "records"}
    lines = ["Current medications: " + ", ".join(f"{m.name}" for m in meds) + "."]
    maoi = [m for m in meds if m.drug_class == "MAOI"]
    if maoi:
        lines.append(f"Important: because you take {maoi[0].name}, some medicines "
                     "(certain migraine, cough and cold, and antidepressant medicines) can be "
                     "dangerous — always check first.")
    evidence = [{"text": f"{m.name} — {m.status.value}", "source": m.source} for m in meds]
    return {"answer": " ".join(lines), "evidence": evidence, "engine": "records"}


@app.post("/api/recall")
def recall(req: RecallRequest, store: PatientStore = Depends(user_store)):
    # Answer from the Cognee memory graph; fall back to the JSON store if unavailable.
    got = cognee_bridge.recall(req.query)
    if got and got.get("answer"):
        return {"answer": got["answer"], "evidence": got.get("evidence", []), "engine": "cognee"}
    return _cited_from_records(store)


@app.post("/api/erase")
def erase(store: PatientStore = Depends(user_store)):
    cognee_bridge.erase()  # right to be forgotten: purge the Cognee graph
    store.clear()
    return {"status": "erased"}


@app.get("/api/memory/status")
def memory_status():
    return {"enabled": cognee_bridge.enabled(), "building": cognee_bridge.is_building()}


# ---------- record management ----------

def _fact_summary(n) -> dict:
    if isinstance(n, Medication):
        detail = " · ".join(b for b in (n.drug_class, n.dose) if b)
        return {"kind": "medication", "label": n.name, "detail": detail,
                "drug_class": n.drug_class, "dose": n.dose,
                "status": n.status.value, "source": n.source}
    if isinstance(n, Condition):
        return {"kind": "condition", "label": n.name, "detail": "",
                "status": n.status.value, "source": n.source}
    if isinstance(n, Allergy):
        return {"kind": "allergy", "label": n.substance, "detail": n.reaction or "",
                "status": "allergy", "source": n.source}
    return {"kind": type(n).__name__.lower(), "label": getattr(n, "name", "?"),
            "detail": "", "status": "", "source": getattr(n, "source", "")}


@app.get("/api/records")
def list_records(store: PatientStore = Depends(user_store)):
    return {"facts": [_fact_summary(n) for n in store.all_facts()],
            "count": len(store.all_facts())}


class TextRecord(BaseModel):
    text: str
    source: str | None = None


@app.post("/api/records/text")
def add_text_record(req: TextRecord, store: PatientStore = Depends(user_store)):
    try:
        added = store.add_from_text(req.text, req.source)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    cognee_bridge.resync(store.all_facts())
    return {"ok": True, "extracted": [_fact_summary(n) for n in added], "count": len(added)}


class ManualRecord(BaseModel):
    kind: str
    data: dict


@app.post("/api/records/manual")
def add_manual_record(req: ManualRecord, store: PatientStore = Depends(user_store)):
    try:
        node = store.add_manual(req.kind, req.data)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    cognee_bridge.resync(store.all_facts())
    return {"ok": True, "added": _fact_summary(node)}


class ManualBatch(BaseModel):
    medications: list[dict] = []
    conditions: list[dict] = []
    allergies: list[dict] = []


@app.post("/api/records/manual/batch")
def add_manual_batch(req: ManualBatch, store: PatientStore = Depends(user_store)):
    """Add medications, conditions, and allergies together in one submission.

    Rows missing their required field (medication/condition name, allergy substance)
    are skipped so the user can leave unused rows blank.
    """
    items: list[tuple[str, dict]] = []
    items += [("medication", m) for m in req.medications if (m.get("name") or "").strip()]
    items += [("condition", c) for c in req.conditions if (c.get("name") or "").strip()]
    items += [("allergy", a) for a in req.allergies if (a.get("substance") or "").strip()]
    if not items:
        return {"ok": False, "error": "Add at least one medication, condition, or allergy."}
    try:
        added = store.add_manual_batch(items)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    cognee_bridge.resync(store.all_facts())
    return {"ok": True, "added": [_fact_summary(n) for n in added], "count": len(added)}


@app.get("/api/notes")
def get_notes(store: PatientStore = Depends(user_store)):
    """Notes newest-first, each with its extracted facts (grouped by note id)."""
    return {"notes": [
        {"id": n["id"], "name": n["name"], "text": n["text"], "created": n["created"],
         "facts": [_fact_summary(f) for f in n["nodes"]]}
        for n in store.notes()
    ]}


class NoteUpdate(BaseModel):
    id: str
    text: str


@app.post("/api/records/note/update")
def update_note(req: NoteUpdate, store: PatientStore = Depends(user_store)):
    try:
        added = store.update_note(req.id, req.text)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    # An edit replaces the note's facts, so rebuild memory from the full current record
    # (a plain add would leave the old, now-removed facts in the graph).
    cognee_bridge.resync(store.all_facts())
    return {"ok": True, "extracted": [_fact_summary(n) for n in added], "count": len(added)}


class NoteDelete(BaseModel):
    id: str


@app.post("/api/records/note/delete")
def delete_note(req: NoteDelete, store: PatientStore = Depends(user_store)):
    try:
        store.delete_note(req.id)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    # Purge the deleted note's facts from memory so they can't resurface in an answer.
    cognee_bridge.resync(store.all_facts())
    return {"ok": True}


@app.post("/api/records/clear")
def clear_records(store: PatientStore = Depends(user_store)):
    store.clear()
    cognee_bridge.erase()  # also wipe the memory graph, not just the JSON store
    return {"ok": True, "count": 0}


@app.get("/api/health")
def health():
    return {"status": "ok", "backend": os.getenv("AEGIS_BACKEND", "mock")}


@app.get("/")
def root():
    return {"service": "Aegis API", "hint": "Open the web app at http://localhost:3000"}
