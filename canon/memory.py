"""CanonMemory — the four memory verbs over a pluggable backend.

`MockMemory` is an in-memory graph so the demo is always green with no keys.
`CogneeMemory` is the real backend — the methods are stubbed with the exact Cognee
call each maps to, so wiring it up is a fill-in-the-blank, not a rewrite.

Day-1 build TODO (from research): confirm forget() cascade semantics on derived edges.
"""

from __future__ import annotations

import os
from typing import Protocol

from .schema import Decision, Symbol, Status


class CanonMemory(Protocol):
    def remember(self, node: Decision | Symbol) -> None: ...
    def recall(self, topic: str) -> list[Decision | Symbol]: ...
    def improve(self, node_id: str, success: bool) -> None: ...
    def forget(self, node_id: str) -> list[str]: ...
    def all_nodes(self) -> list[Decision | Symbol]: ...


class MockMemory:
    """Deterministic in-memory backend for the demo and tests."""

    def __init__(self) -> None:
        self._nodes: dict[str, Decision | Symbol] = {}

    def remember(self, node: Decision | Symbol) -> None:
        self._nodes[node.id] = node

    def recall(self, topic: str) -> list[Decision | Symbol]:
        # Canon only surfaces ACTIVE truth, ranked by improve()-driven weight.
        hits = [
            n for n in self._nodes.values()
            if getattr(n, "topic", getattr(n, "library", "")) == topic
            and n.status == Status.ACTIVE
        ]
        return sorted(hits, key=lambda n: n.weight, reverse=True)

    def improve(self, node_id: str, success: bool) -> None:
        node = self._nodes.get(node_id)
        if node:
            node.weight = max(0.0, node.weight + (0.5 if success else -0.5))

    def forget(self, node_id: str) -> list[str]:
        """Retire a node and cascade to anything that pointed at it. Returns removed ids."""
        removed = []
        node = self._nodes.pop(node_id, None)
        if node:
            removed.append(node_id)
            # cascade: drop derived edges/nodes referencing the forgotten one
            for other in list(self._nodes.values()):
                ref = getattr(other, "superseded_by", None) or getattr(other, "replacement", None)
                if ref == node_id:
                    if isinstance(other, Decision):
                        other.superseded_by = None
                    else:
                        other.replacement = None
        return removed

    def all_nodes(self) -> list[Decision | Symbol]:
        return list(self._nodes.values())


class CogneeMemory:
    """Real backend. Each method documents the exact Cognee call it maps to."""

    def __init__(self) -> None:
        import cognee  # noqa: F401  (imported lazily so mock mode needs no install)
        self._cognee = cognee

    def remember(self, node: Decision | Symbol) -> None:
        # await cognee.add(node.model_dump()); await cognee.cognify()
        raise NotImplementedError("wire cognee.add + cognify")

    def recall(self, topic: str) -> list[Decision | Symbol]:
        # await cognee.search(query_text=topic, query_type=SearchType.GRAPH_COMPLETION)
        raise NotImplementedError("wire cognee.search (hybrid graph+vector)")

    def improve(self, node_id: str, success: bool) -> None:
        # cognee feedback loop: re-weight edges / update node props for node_id
        raise NotImplementedError("wire cognee improve()/memify feedback")

    def forget(self, node_id: str) -> list[str]:
        # await cognee.delete(data_id=node_id)  # validate cascade on derived edges
        raise NotImplementedError("wire cognee.forget/delete")

    def all_nodes(self) -> list[Decision | Symbol]:
        raise NotImplementedError("wire graph dump for the visualizer")


def get_memory() -> CanonMemory:
    backend = os.getenv("CANON_BACKEND", "mock").lower()
    return CogneeMemory() if backend == "cognee" else MockMemory()
