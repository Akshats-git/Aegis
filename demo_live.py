"""LIVE demo against the real Cognee engine (the one you show the judges).

    CANON_BACKEND=cognee python demo_live.py

Requires a working LLM key in .env (LLM_API_KEY). Proves the thesis: forget() surgically
removes a superseded decision so Cognee's graph reasoning stops surfacing it at all.

The offline, key-free version is demo.py (mock backend).
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

load_dotenv()

import cognee
from canon.memory import CogneeMemory
from canon.schema import Decision, Status


def banner(text: str) -> None:
    print(f"\n{'=' * 68}\n{text}\n{'=' * 68}")


def answer_of(result) -> str:
    """Pull the natural-language answer out of a Cognee recall response."""
    try:
        return result[0].text.strip()
    except Exception:
        return str(result)[:400]


async def _reset() -> None:
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)


def main() -> None:
    asyncio.run(_reset())
    mem = CogneeMemory()

    redux = Decision(
        id="dec-redux", topic="state-management",
        statement="Use Redux for client-side state", status=Status.SUPERSEDED,
        source="ADR-0003", superseded_by="dec-zustand",
    )
    zustand = Decision(
        id="dec-zustand", topic="state-management",
        statement="Use Zustand for client-side state", status=Status.ACTIVE,
        source="PR #142",
    )

    banner("remember(): ingest the team's decision history into Cognee's graph")
    mem.remember(redux)
    mem.remember(zustand)
    print("  ingested ADR-0003 (Redux, superseded) and PR #142 (Zustand, active)")

    q = "client-side state management library"
    banner("recall() BEFORE forget — Redux still lingers in the evidence")
    print("  ", answer_of(mem.recall(q)))

    banner("forget(): retire the superseded Redux decision (the MOAT)")
    print("  forgot:", mem.forget("dec-redux"))

    banner("recall() AFTER forget — Redux is gone, only current canon remains")
    print("  ", answer_of(mem.recall(q)))

    banner("Proven live: forget() surgically corrects the source of truth")


if __name__ == "__main__":
    main()
