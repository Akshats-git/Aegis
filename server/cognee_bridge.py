"""Bridge between the web app and the Cognee memory layer.

Cognee is the app's persistent, self-correcting memory: one shared clinical graph for the
record this instance manages. It is single-tenant; see aegis/memory.py for the reason. When
records change the graph is resynced in the background, because the graph build is slow and
must not block the request. Three features read from it: "Ask Aegis" (recall), the safety
check's broad assessment (assess), and account erasure (erase).

Everything here is best-effort. If Cognee or the LLM is unavailable, callers fall back to
fast deterministic logic and the app keeps working.
"""

from __future__ import annotations

import json
import os
import re
import threading

_lock = threading.Lock()
_building = False
_building_lock = threading.Lock()

ASSESS_SYSTEM_PROMPT = (
    "You are a clinical medication-safety assistant supporting a doctor making an urgent "
    "treatment decision. Using ONLY the patient facts in the provided context, assess "
    "whether the proposed new medicine is safe. Identify clinically significant drug-drug "
    "interactions, drug-condition contraindications, and allergy risks. Respond with ONLY a "
    "JSON object, no prose before or after it, of the form: "
    '{"drug_class": string, "concerns": [{"severity": "life-threatening"|"severe"|'
    '"moderate"|"mild", "concern": short title, "reason": one plain-English sentence, '
    '"related_to": the specific current medicine, condition or allergy it relates to}], '
    '"safe_alternatives": [string]}. List only real, clinically significant concerns '
    "grounded in the patient's actual record; if there are none, return an empty concerns "
    "list. Be conservative: only report interactions that are well-established and "
    "clinically significant in standard references."
)


def enabled() -> bool:
    return bool(os.getenv("LLM_API_KEY")) and os.getenv("AEGIS_COGNEE", "1") != "0"


def is_building() -> bool:
    with _building_lock:
        return _building


def _set_building(on: bool) -> None:
    global _building
    with _building_lock:
        _building = on


def resync(nodes: list) -> None:
    """Rebuild the memory graph so it holds exactly the current, reconciled record.

    First ingest every fact, so the forget() calls during reconciliation have a real
    data_id to act on. Then reconcile, which issues a forget() call for each stale fact.
    Single-item forget() does not purge the graph or vector store in this version of Cognee,
    so when reconciliation dropped anything, also rebuild from just the clean list. That
    guarantees a forgotten fact cannot resurface in a later answer while still running a
    real forget() call per stale fact.
    """
    if not enabled():
        return
    items = list(nodes)
    # Set this synchronously, not inside the thread, so a recall() or is_building() call
    # made right after resync() returns cannot race ahead of the rebuild and observe the
    # graph mid-erase.
    _set_building(True)

    def _run():
        try:
            with _lock:
                from aegis.memory import CogneeMemory
                from aegis.reconcile import reconcile
                mem = CogneeMemory()
                mem.erase()
                for n in items:
                    try:
                        mem.remember(n)
                    except Exception:
                        pass
                _, clean = reconcile(items, mem)  # real forget() on each stale fact's data_id
                if len(clean) != len(items):
                    mem.erase()
                    for n in clean:
                        try:
                            mem.remember(n)
                        except Exception:
                            pass
                if items:
                    try:
                        mem.improve()
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            _set_building(False)

    threading.Thread(target=_run, daemon=True).start()


def recall(query: str) -> dict | None:
    """Answer from the Cognee graph. Returns {answer, evidence} or None on failure."""
    if not enabled():
        return None
    try:
        with _lock:
            from aegis.memory import CogneeMemory, parse_recall_answer
            res = CogneeMemory().recall(query)
        if not res:
            return None
        raw = getattr(res[0], "text", "") or ""
        if not raw:
            return None
        answer, evidence = parse_recall_answer(raw)
        return {"answer": answer, "evidence": evidence}
    except Exception:
        return None


def assess(name: str, indication: str | None = None) -> dict | None:
    """Graph-grounded broad safety assessment, cited from the record's own Cognee memory.

    Reuses recall()'s GRAPH_COMPLETION with a custom system prompt that asks for a
    structured verdict instead of prose, so the same cited, graph-reasoned pipeline behind
    "Ask Aegis" also powers the safety check's AI layer. Returns None (and the caller falls
    back to a direct LLM call) if Cognee is unavailable or the answer is not valid JSON. The
    deterministic interaction rules remain the safety-critical authority either way.
    """
    if not enabled():
        return None
    query = (
        f"A clinician is considering prescribing {name} for this patient"
        + (f", for {indication}" if indication else "")
        + ". Assess whether it is safe given everything on record."
    )
    try:
        with _lock:
            from aegis.memory import CogneeMemory, parse_recall_answer
            res = CogneeMemory().recall(query, system_prompt=ASSESS_SYSTEM_PROMPT)
        if not res:
            return None
        raw = getattr(res[0], "text", "") or ""
        if not raw:
            return None
        answer, evidence = parse_recall_answer(raw)
        match = re.search(r"\{.*\}", answer, re.S)
        data = json.loads(match.group(0) if match else answer)
        data["_evidence"] = evidence
        return data
    except Exception:
        return None


def erase() -> None:
    """Purge the Cognee memory (right to be forgotten). Best-effort."""
    if not enabled():
        return
    try:
        with _lock:
            from aegis.memory import CogneeMemory
            CogneeMemory().erase()
    except Exception:
        pass
