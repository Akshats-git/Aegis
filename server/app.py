"""Aegis API.

    uvicorn server.app:app --reload --port 8000

The deterministic endpoints (patient, timeline, reconcile, handoff, safety-check) are
instant and always work — they power the UI. The /recall and /erase endpoints use the real
Cognee memory when AEGIS_BACKEND=cognee (after /seed); otherwise they fall back to an
honest, cited answer assembled from the structured records so the UI is never blocked.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # make LLM_API_KEY etc. available for text extraction and Cognee

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aegis import Medication, Condition, Allergy, ClinicalStatus
from aegis.sample_patient import PROPOSED_DRUG
from aegis.reconcile import reconcile, current_medications, ReconcileAction
from aegis.interactions import check, suggest_alternatives, CANDIDATE_DRUGS
from aegis.report import handoff_summary
from aegis.memory import MockMemory
from server.store import store

app = FastAPI(title="Aegis API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PATIENT = {"name": "Margaret Chen", "age": 58, "sex": "F", "mrn": "SYN-0001",
           "note": "synthetic patient — no real data"}


def _reconciled():
    """Return (actions, clean_nodes) over the current patient store (instant)."""
    mem = MockMemory()
    nodes = store.all_facts()
    for n in nodes:
        mem.remember(n)
    return reconcile(nodes, mem), nodes


# ---------- deterministic endpoints (instant) ----------

@app.get("/api/patient")
def get_patient():
    return {"patient": PATIENT, "documents": store.documents}


@app.get("/api/timeline")
def get_timeline():
    (_, clean), all_nodes = _reconciled()
    meds = []
    for n in all_nodes:
        if isinstance(n, Medication):
            meds.append({
                "id": n.id, "name": n.name, "drug_class": n.drug_class,
                "dose": n.dose, "status": n.status.value,
                "started": n.started, "stopped": n.stopped,
                "source": n.source,
                "forgotten": n.id not in {c.id for c in clean},
                "danger": n.drug_class == "MAOI" and n.status == ClinicalStatus.ACTIVE,
            })
    meds.sort(key=lambda m: m["started"] or "")
    return {"medications": meds}


@app.get("/api/reconcile")
def get_reconcile():
    (actions, clean), _ = _reconciled()
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
def get_handoff():
    (_, clean), _ = _reconciled()
    conditions = [n.name for n in clean if isinstance(n, Condition) and n.status == ClinicalStatus.ACTIVE]
    meds = [{"name": m.name, "dose": m.dose, "drug_class": m.drug_class}
            for m in current_medications(clean)]
    allergies = [{"substance": a.substance, "reaction": a.reaction}
                 for a in clean if isinstance(a, Allergy)]
    discontinued = [{"name": n.name, "stopped": n.stopped}
                    for n in clean if isinstance(n, Medication) and n.status == ClinicalStatus.DISCONTINUED]
    return {"conditions": conditions, "medications": meds, "allergies": allergies,
            "discontinued": discontinued, "text": handoff_summary(clean)}


@app.get("/api/candidates")
def get_candidates():
    return {"candidates": CANDIDATE_DRUGS, "default": PROPOSED_DRUG}


class SafetyRequest(BaseModel):
    name: str
    drug_class: str
    indication: str | None = "migraine"


@app.post("/api/safety-check")
def safety_check(req: SafetyRequest):
    (_, clean), _ = _reconciled()
    current = current_medications(clean)
    allergies = [n for n in clean if isinstance(n, Allergy)]
    alerts = check(req.name, req.drug_class, current, allergies)
    blocking = any(a.is_blocking for a in alerts)
    return {
        "proposed": {"name": req.name, "drug_class": req.drug_class},
        "verdict": "block" if blocking else "ok",
        "alerts": [{
            "severity": a.severity.value, "effect": a.effect,
            "proposed_drug": a.proposed_drug, "conflicting_drug": a.conflicting_drug,
            "mechanism": a.mechanism, "management": a.management,
            "patient_source": a.patient_source, "evidence_source": a.evidence_source,
        } for a in alerts],
        "alternatives": suggest_alternatives(req.indication or "migraine") if blocking else [],
    }


# ---------- Cognee-backed endpoints (real memory when enabled) ----------

class RecallRequest(BaseModel):
    query: str = "List this patient's current medications and what to avoid prescribing."


def _cited_from_records(query: str) -> dict:
    """Honest fallback: assemble a cited answer from the structured records (instant)."""
    (_, clean), _ = _reconciled()
    meds = current_medications(clean)
    lines = [f"Current medications: " +
             ", ".join(f"{m.name} [{m.drug_class}]" for m in meds) + "."]
    maoi = [m for m in meds if m.drug_class == "MAOI"]
    if maoi:
        lines.append(f"Caution: active MAOI ({maoi[0].name}) — avoid triptans, SSRIs/SNRIs, "
                     "sympathomimetics and dextromethorphan (serotonin syndrome / "
                     "hypertensive crisis).")
    evidence = [{"text": f"{m.name} [{m.drug_class}] — {m.status.value}", "source": m.source}
                for m in meds]
    return {"answer": " ".join(lines), "evidence": evidence, "engine": "records"}


@app.post("/api/recall")
def recall(req: RecallRequest):
    if os.getenv("AEGIS_BACKEND", "mock").lower() == "cognee":
        try:
            from aegis.memory import CogneeMemory
            mem = CogneeMemory()
            res = mem.recall(req.query)
            answer = res[0].text if res else ""
            evidence = []
            for e in (res or []):
                for ref in getattr(e, "references", None) or []:
                    evidence.append({"text": str(getattr(ref, "text", ref))[:200], "source": "graph"})
            if answer:
                return {"answer": answer, "evidence": evidence, "engine": "cognee"}
        except Exception as e:
            return {"answer": "", "evidence": [], "engine": "cognee-error", "error": str(e)[:200]}
    return _cited_from_records(req.query)


@app.post("/api/erase")
def erase():
    """Right to be forgotten. Real erasure when Cognee is enabled + seeded."""
    if os.getenv("AEGIS_BACKEND", "mock").lower() == "cognee":
        try:
            from aegis.memory import CogneeMemory
            CogneeMemory().erase()
            return {"status": "erased", "engine": "cognee"}
        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}
    return {"status": "erased", "engine": "simulated"}


# ---------- record management (users add their own records) ----------

def _fact_summary(n) -> dict:
    if isinstance(n, Medication):
        return {"kind": "medication", "label": f"{n.name} [{n.drug_class}]",
                "status": n.status.value, "source": n.source}
    if isinstance(n, Condition):
        return {"kind": "condition", "label": n.name, "status": n.status.value, "source": n.source}
    if isinstance(n, Allergy):
        return {"kind": "allergy", "label": n.substance, "status": "allergy", "source": n.source}
    return {"kind": type(n).__name__.lower(), "label": getattr(n, "name", "?"),
            "status": "", "source": getattr(n, "source", "")}


@app.get("/api/records")
def list_records():
    return {"facts": [_fact_summary(n) for n in store.all_facts()],
            "count": len(store.all_facts())}


class TextRecord(BaseModel):
    text: str
    source: str | None = None


@app.post("/api/records/text")
def add_text_record(req: TextRecord):
    try:
        added = store.add_from_text(req.text, req.source)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    return {"ok": True, "extracted": [_fact_summary(n) for n in added], "count": len(added)}


class ManualRecord(BaseModel):
    kind: str            # "medication" | "condition" | "allergy"
    data: dict


@app.post("/api/records/manual")
def add_manual_record(req: ManualRecord):
    try:
        node = store.add_manual(req.kind, req.data)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    return {"ok": True, "added": _fact_summary(node)}


@app.post("/api/records/reset")
def reset_records():
    store.reset()
    return {"ok": True, "count": len(store.all_facts())}


@app.post("/api/records/clear")
def clear_records():
    store.clear()
    return {"ok": True, "count": 0}


@app.get("/api/health")
def health():
    return {"status": "ok", "backend": os.getenv("AEGIS_BACKEND", "mock")}


@app.get("/")
def root():
    return {
        "service": "Aegis API",
        "hint": "This is the backend. Open the web app at http://localhost:3000",
        "docs": "/docs",
        "endpoints": [
            "/api/patient", "/api/timeline", "/api/reconcile", "/api/handoff",
            "/api/candidates", "/api/safety-check", "/api/recall", "/api/erase",
        ],
    }


@app.get("/favicon.ico")
def favicon():
    from fastapi import Response
    return Response(status_code=204)
