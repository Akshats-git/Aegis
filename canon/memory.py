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
    # recall returns structured nodes on the mock backend and Cognee response
    # entries on the real backend, so it is intentionally untyped here.
    def remember(self, node: Decision | Symbol) -> None: ...
    def recall(self, topic: str): ...
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
    """Real backend, wired against the verified cognee 1.2 async API.

    Design: each forgettable node lives in its own dataset ``canon_<id>`` so
    ``forget(dataset=...)`` targets exactly one node, while ``recall`` still reasons
    across the whole graph via GRAPH_COMPLETION. The v1 verbs (remember/recall/
    improve/forget) are used directly — that's the hackathon theme.

    STATUS: wired but pending one live validation run (blocked on a valid LLM key).
    Verified so far: signatures match, embeddings run locally, pipeline reaches the LLM.
    """

    def __init__(self) -> None:
        import asyncio
        import cognee
        from cognee.modules.search.types import SearchType

        self._cognee = cognee
        self._SearchType = SearchType
        self._run = asyncio.run
        self._ds = lambda node_id: f"canon_{node_id}".replace(" ", "_")

    def _describe(self, node: Decision | Symbol) -> str:
        """Render a node as text so cognify extracts its entities and relations."""
        if isinstance(node, Decision):
            base = f"Decision {node.id} (topic: {node.topic}): {node.statement}. Source {node.source}. Status: {node.status.value}."
            if node.superseded_by:
                base += f" This supersedes / is superseded in favor of {node.superseded_by}."
            return base
        base = f"API symbol {node.library}.{node.name} (id {node.id}), introduced {node.version_introduced}, status {node.status.value}."
        if node.version_removed:
            base += f" Removed in {node.version_removed}."
        if node.replacement:
            base += f" Replaced by {node.replacement}."
        return base

    def remember(self, node: Decision | Symbol) -> None:
        # v1 verb: add + cognify + optional self-improvement in one call
        self._run(self._cognee.remember(self._describe(node), dataset_name=self._ds(node.id)))

    def recall(self, topic: str):
        # hybrid graph+vector reasoning over the whole graph
        return self._run(
            self._cognee.recall(
                query_text=f"What is the current canonical answer for: {topic}? Ignore superseded or removed items.",
                query_type=self._SearchType.GRAPH_COMPLETION,
                include_references=True,
            )
        )

    def improve(self, node_id: str, success: bool) -> None:
        # enrich/re-weight the node's dataset (feedback influence flows through recall too)
        self._run(self._cognee.improve(dataset=self._ds(node_id)))

    def forget(self, node_id: str) -> list[str]:
        # remove exactly this node's dataset. Day-1 TODO: confirm derived edges cascade.
        self._run(self._cognee.forget(dataset=self._ds(node_id)))
        return [node_id]

    def all_nodes(self):  # graph dump for the visualizer — best-effort, wire when needed
        raise NotImplementedError("expose graph via cognee graph API for the visualizer")


def get_memory() -> CanonMemory:
    backend = os.getenv("CANON_BACKEND", "mock").lower()
    return CogneeMemory() if backend == "cognee" else MockMemory()
