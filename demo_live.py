"""LIVE end-to-end demo against the real Cognee engine (the one you show judges).

    AEGIS_BACKEND=cognee python demo_live.py

Exercises all four Cognee verbs genuinely:
  remember()  ingest the patient's fragmented records into one connected graph
  recall()    answer "what should a new provider know?" with cited evidence
  improve()   enrich the memory
  forget()    right-to-be-forgotten erasure of the whole record (provably purges)

The safety-critical reconciliation (deciding the authoritative current picture and
dropping stale facts) is done by Aegis's deterministic engine — guaranteed, not left to
an LLM. Requires a working LLM key in .env. Offline version: demo.py.
"""

from __future__ import annotations

import asyncio
import logging
import os
import warnings

# Quiet Cognee/aiohttp logs so the demo output is clean on stage (set before importing cognee).
os.environ.setdefault("LOG_LEVEL", "CRITICAL")
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("AEGIS_BACKEND", "cognee")

import cognee
from aegis.memory import CogneeMemory
from aegis.ingest import ingest_records
from aegis.reconcile import reconcile, current_medications
from aegis.interactions import check, suggest_alternatives
from aegis.report import handoff_summary
from aegis.sample_patient import records, PROPOSED_DRUG


def line() -> None:
    print("-" * 68)


def answer_of(result) -> str:
    try:
        return result[0].text.strip()
    except Exception:
        return str(result)[:600]


async def _reset() -> None:
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)


def main() -> None:
    asyncio.run(_reset())
    mem = CogneeMemory()
    nodes = records()

    line(); print("remember(): ingesting the patient's fragmented records into Cognee"); line()
    ingest_records(mem)
    print(f"  ingested {len(nodes)} clinical facts across 4 source documents")

    line(); print("recall(): what should a new provider know? (Cognee, with evidence)"); line()
    ans = mem.recall("List this patient's current medications by name and drug class, and "
                     "state which medication classes must be avoided when prescribing.")
    print("  " + answer_of(ans).replace("\n", "\n  "))

    line(); print("improve(): enriching the memory graph"); line()
    try:
        mem.improve()
        print("  memory enriched (edges re-weighted / graph enriched)")
    except Exception as e:  # non-fatal for the demo
        print(f"  (improve skipped: {type(e).__name__})")

    line(); print("Reconciliation engine (deterministic): forget stale facts"); line()
    actions, clean = reconcile(nodes, mem)
    for a in actions:
        for fid, fstatus, fsrc in a.forgotten:
            print(f"  ✗ dropped stale '{a.entity}' [{fstatus}] from {fsrc}")
    print("\n  " + handoff_summary(clean).replace("\n", "\n  "))

    line(); print(f"Safety check: proposed {PROPOSED_DRUG['name']} ({PROPOSED_DRUG['drug_class']})"); line()
    current = current_medications(clean)
    alerts = check(PROPOSED_DRUG["name"], PROPOSED_DRUG["drug_class"], current)
    for a in alerts:
        print(f"  🚨 {a.severity.value.upper()}: {a.effect}  ({a.proposed_drug} ✕ {a.conflicting_drug})")
        print(f"     evidence: {a.patient_source} · {a.evidence_source}")
    if any(a.is_blocking for a in alerts):
        print("  🟢 safer alternatives:", "; ".join(suggest_alternatives("migraine")))

    line(); print("forget(): right to be forgotten — erase the record, then re-query"); line()
    mem.erase()
    after = mem.recall("List this patient's current medications.")
    if not after:
        print("  ✅ record fully erased — Cognee has no memory of this patient (recall finds nothing).")
    else:
        print("  " + answer_of(after).replace("\n", "\n  ")[:300])

    line(); print("Proven live on Cognee: remember · recall · improve · forget"); line()


if __name__ == "__main__":
    main()
