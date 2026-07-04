"""Bridge between the web app and the Cognee memory layer.

Cognee is the app's persistent, self-correcting memory. When a user adds records we ingest
them into that user's Cognee dataset in the background (Cognee's graph build is slow, so it
must not block the request). "Ask Aegis" then answers from that graph, and deleting the
account purges it via Cognee's forget().

Everything here is best-effort: if Cognee or the LLM is unavailable, callers fall back to
the fast JSON store, so the app keeps working.
"""

from __future__ import annotations

import os
import re
import threading
from collections import defaultdict

# Serialize Cognee writes per user so overlapping ingests don't clash.
_locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)
# Track users with an ingest in flight, so the UI can show a "building memory" state.
_building: set[str] = set()
_building_lock = threading.Lock()


def enabled() -> bool:
    return bool(os.getenv("LLM_API_KEY")) and os.getenv("AEGIS_COGNEE", "1") != "0"


def is_building(user_id: str) -> bool:
    with _building_lock:
        return user_id in _building


def _set_building(user_id: str, on: bool) -> None:
    with _building_lock:
        (_building.add if on else _building.discard)(user_id)


def resync(user_id: str, nodes: list) -> None:
    """Rebuild the memory graph so it holds exactly the current records, nothing else.

    In this Cognee version the knowledge graph is a single shared store and recall's
    graph-completion ignores the ``datasets`` filter, so a plain incremental add would let
    old or deleted facts keep leaking into answers. On every change we therefore prune the
    whole graph (via ``CogneeMemory.erase``) and re-ingest the full current record. That
    keeps recall honest: a forgotten fact can never resurface. Runs in the background because
    the rebuild is slow, and runs even when the record list is now empty, so deleting the
    last note also clears memory.
    """
    if not enabled():
        return
    items = list(nodes)

    def _run():
        _set_building(user_id, True)
        try:
            with _locks[user_id]:
                from aegis.memory import CogneeMemory
                mem = CogneeMemory(user_id)
                mem.erase()  # drop the stale graph first
                for n in items:
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
            _set_building(user_id, False)

    threading.Thread(target=_run, daemon=True).start()


def _parse_answer(raw: str) -> tuple[str, list[dict]]:
    """Split Cognee's answer from its embedded 'Evidence:' section into clean citations."""
    parts = re.split(r"\n\s*Evidence:\s*", raw, maxsplit=1, flags=re.I)
    answer = parts[0].strip()
    evidence: list[dict] = []
    if len(parts) > 1:
        for line in parts[1].splitlines():
            line = line.strip()
            if not line.startswith("-"):
                continue
            # each line: - chunk ... (data_id: ...): "the fact text (source: ...)"
            m = re.search(r':\s*"(.*)$', line)
            if not m:
                continue
            text = m.group(1).strip().strip('"').rstrip("…").strip()
            if not text:
                continue
            source = "your records"
            sm = re.search(r"\(source:\s*([^)]*)\)", text)
            if sm:
                source = sm.group(1).strip()
                text = text[: sm.start()].strip().rstrip(".").strip()
            evidence.append({"text": text, "source": source})
    return answer, evidence


def recall(user_id: str, query: str) -> dict | None:
    """Answer from the user's Cognee graph. Returns {answer, evidence} or None on failure."""
    if not enabled():
        return None
    try:
        with _locks[user_id]:
            from aegis.memory import CogneeMemory
            res = CogneeMemory(user_id).recall(query)
        if not res:
            return None
        raw = getattr(res[0], "text", "") or ""
        if not raw:
            return None
        answer, evidence = _parse_answer(raw)
        return {"answer": answer, "evidence": evidence}
    except Exception:
        return None


def erase(user_id: str) -> None:
    """Purge the user's Cognee dataset (right to be forgotten). Best-effort."""
    if not enabled():
        return
    try:
        with _locks[user_id]:
            from aegis.memory import CogneeMemory
            CogneeMemory(user_id).erase()
    except Exception:
        pass
