"""End-to-end demo: the 'reversed decision' + 'removed API' story, all four verbs.

    python demo.py

Runs on the mock backend by default (no keys). Set CANON_BACKEND=cognee to use Cognee.
"""

from __future__ import annotations

from canon import get_memory, ingest_all
from canon.schema import Status


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def naive_rag(mem, topic: str) -> str:
    """What a stateless retriever does: returns the most-mentioned match, status-blind."""
    hits = [n for n in mem.all_nodes()
            if getattr(n, "topic", getattr(n, "library", "")) == topic]
    # 'most mentioned' here ~ the older, more-cited decision (the classic failure mode)
    return min(hits, key=lambda n: n.source).statement if hits else "(nothing)"


def main() -> None:
    mem = get_memory()

    banner("remember(): ingest ADRs / PRs / changelogs into the Canon graph")
    ingest_all(mem)
    print(f"  ingested {len(mem.all_nodes())} nodes")

    banner("The problem: naive retrieval is confidently WRONG")
    print(f"  Q: which state library do we use?")
    print(f"  naive RAG  -> {naive_rag(mem, 'state-management')}   # the REVERSED decision")

    banner("recall(): Canon returns only CURRENT truth")
    for n in mem.recall("state-management"):
        print(f"  canon      -> {n.statement}   (source {n.source}, weight {n.weight})")

    banner("improve(): a code review upholds the Zustand decision")
    mem.improve("dec-zustand", success=True)
    print(f"  dec-zustand weight is now {next(n.weight for n in mem.all_nodes() if n.id=='dec-zustand')}")

    banner("forget(): retire the reversed Redux decision (the MOAT)")
    before = len(mem.all_nodes())
    removed = mem.forget("dec-redux")
    print(f"  forgot {removed}; nodes {before} -> {len(mem.all_nodes())}")
    print(f"  naive RAG can no longer resurface it: {naive_rag(mem, 'state-management')}")

    banner("Same mechanic for a REMOVED public API (the relatable hook)")
    print(f"  before bump, agent might suggest: openai.Completion.create  (status: removed)")
    mem.forget("sym-openai-completion")
    valid = mem.recall("openai")
    print(f"  after forget(), only valid API recalled: {valid[0].name if valid else '(none)'}")

    banner("Done — all four verbs exercised; forget()/improve() are the stars")


if __name__ == "__main__":
    main()
