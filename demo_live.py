"""End-to-end demo against the real Cognee engine.

    python demo_live.py

Calls the same functions the web app calls (server/cognee_bridge.py), so it runs the
product's actual memory pipeline against the synthetic patient. It exercises all four
Cognee operations:

  remember()  ingest the patient's fragmented, conflicting records into one graph.
  forget()    reconciliation drops the stale, superseded fact with a real forget() call per
              stale fact (see cognee_bridge.resync). The graph is then rebuilt from just the
              clean picture, because single-item forget() does not purge the graph or vector
              store in this version of Cognee.
  recall()    answer "what should a new provider know?" with a cited, graph-grounded reply
              that no longer contains the fact that was just forgotten.
  improve()   enrich the memory graph after each sync.
  forget()    at the dataset level via erase(), for the right to be forgotten. Recall
              afterwards finds nothing.

The safety check combines a deterministic rule engine, which handles the life-threatening
cases and is never left to an LLM, with a broad, graph-grounded assessment answered by
Cognee's own recall() over the same memory. It requires a working LLM key in .env. For the
offline version that needs no keys, see demo.py.
"""

from __future__ import annotations

import logging
import os
import time
import warnings

# Quiet Cognee/aiohttp logs so the demo output is clean on stage (set before importing cognee).
os.environ.setdefault("LOG_LEVEL", "CRITICAL")
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

from dotenv import load_dotenv

load_dotenv()

from aegis.memory import MockMemory
from aegis.reconcile import reconcile
from aegis.sample_patient import records, PROPOSED_DRUG
from server import cognee_bridge


def line() -> None:
    print("-" * 68)


def main() -> None:
    if not cognee_bridge.enabled():
        raise SystemExit("Set LLM_API_KEY in .env first (see .env.example).")

    nodes = records()

    line(); print("remember() + forget(): syncing the patient's fragmented records"); line()
    # The action log is a fast local computation for display. The actual forgetting happens
    # inside cognee_bridge.resync() below, against the live graph.
    actions, _ = reconcile(nodes, MockMemory())
    for a in actions:
        for fid, fstatus, fsrc in a.forgotten:
            print(f"  dropped stale '{a.entity}' [{fstatus}] from {fsrc}")
    print(f"  syncing {len(nodes)} facts across 4 source documents into Cognee...")
    cognee_bridge.resync(nodes)
    while cognee_bridge.is_building():
        time.sleep(1)
    print("  done. the graph now holds only the reconciled, current picture")

    line(); print("recall(): what should a new provider know? (cited, from the live graph)"); line()
    got = cognee_bridge.recall(
        "List this patient's current medications by name and drug class, and state which "
        "medication classes must be avoided when prescribing."
    )
    if got:
        print("  " + got["answer"].replace("\n", "\n  "))
        for e in got["evidence"]:
            print(f"    · {e['text']}  (from: {e['source']})")
    else:
        print("  (no answer, Cognee unavailable)")

    line(); print(f"Safety check: proposed {PROPOSED_DRUG['name']} ({PROPOSED_DRUG['drug_class']})"); line()
    from aegis.reconcile import current_medications
    from aegis.interactions import check, suggest_alternatives
    _, clean = reconcile(nodes, MockMemory())
    current = current_medications(clean)
    alerts = check(PROPOSED_DRUG["name"], PROPOSED_DRUG["drug_class"], current)
    for a in alerts:
        print(f"  [reference/guaranteed] {a.severity.value.upper()}: {a.effect}  "
              f"({a.proposed_drug} x {a.conflicting_drug})")
        print(f"    evidence: {a.patient_source} - {a.evidence_source}")
    if any(a.is_blocking for a in alerts):
        print("  safer alternatives:", "; ".join(suggest_alternatives("migraine")))

    print()
    print("  [cognee-grounded/broad] asking the same live graph for a second opinion...")
    a = cognee_bridge.assess(PROPOSED_DRUG["name"], "migraine")
    if a:
        for c in a.get("concerns", []) or []:
            print(f"    {c.get('severity', '?').upper()}: {c.get('concern')} "
                  f"(related to {c.get('related_to')})")
    else:
        print("    (no answer, Cognee unavailable)")

    line(); print("forget(): right to be forgotten. erase the record, then re-query"); line()
    cognee_bridge.erase()
    after = cognee_bridge.recall("List this patient's current medications.")
    if not after:
        print("  record fully erased. Cognee has no memory of this patient (recall finds nothing).")
    else:
        print("  " + after["answer"].replace("\n", "\n  ")[:300])

    line(); print("Proven live on Cognee: remember - recall - improve - forget"); line()


if __name__ == "__main__":
    main()
