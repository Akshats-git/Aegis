"""AegisMemory — the four memory verbs over the patient's clinical graph.

`MockMemory` is an in-memory version so tests/demos run with no keys.
`CogneeMemory` is the real backend (validated end-to-end in earlier work): each verb maps
to a real Cognee call, and each forgettable fact lives in its own dataset so forget()
can retire exactly one fact while recall still reasons across the whole graph.
"""

from __future__ import annotations

import os
from typing import Iterable, Protocol

from .schema import ClinicalNode, ClinicalStatus, Medication


class AegisMemory(Protocol):
    def remember(self, node: ClinicalNode) -> None: ...
    def recall(self, query: str): ...
    def improve(self, node_id: str) -> None: ...
    def forget(self, node_id: str) -> list[str]: ...
    def all_nodes(self) -> list[ClinicalNode]: ...
    def active(self) -> list[ClinicalNode]: ...


def describe(node: ClinicalNode) -> str:
    """Render a clinical fact as a sentence so Cognee can extract entities + relations."""
    src = f" (source: {node.source})"
    if isinstance(node, Medication):
        s = f"Medication {node.name}"
        if node.drug_class:
            s += f" [{node.drug_class}]"
        if node.dose:
            s += f", dose {node.dose}"
        s += f". Status: {node.status.value}."
        if node.started:
            s += f" Started {node.started}."
        if node.stopped:
            s += f" Stopped {node.stopped}."
        if node.reason:
            s += f" Reason: {node.reason}."
        return s + src
    kind = type(node).__name__
    fields = node.model_dump(exclude={"id", "source"})
    body = ", ".join(f"{k}: {v}" for k, v in fields.items() if v is not None)
    return f"{kind} — {body}.{src}"


class MockMemory:
    """Deterministic in-memory backend for offline demos and tests."""

    def __init__(self) -> None:
        self._nodes: dict[str, ClinicalNode] = {}

    def remember(self, node: ClinicalNode) -> None:
        self._nodes[node.id] = node

    def remember_all(self, nodes: Iterable[ClinicalNode]) -> None:
        for n in nodes:
            self.remember(n)

    def remember_text(self, text: str, source: str) -> None:
        # mock backend keeps only structured facts; raw text is a no-op here
        pass

    def recall(self, query: str) -> list[ClinicalNode]:
        # naive keyword recall over ACTIVE facts (real reasoning lives in CogneeMemory)
        q = query.lower()
        return [n for n in self.active()
                if any(q in str(v).lower() for v in n.model_dump().values())]

    def improve(self, node_id: str) -> None:  # mock: no-op enrichment hook
        pass

    def forget(self, node_id: str) -> list[str]:
        return [node_id] if self._nodes.pop(node_id, None) else []

    def all_nodes(self) -> list[ClinicalNode]:
        return list(self._nodes.values())

    def active(self) -> list[ClinicalNode]:
        return [n for n in self._nodes.values()
                if getattr(n, "status", ClinicalStatus.ACTIVE) == ClinicalStatus.ACTIVE]


class CogneeMemory:
    """Real backend, wired against the cognee 1.2 async API (validated in prior work)."""

    def __init__(self) -> None:
        import asyncio
        import cognee
        from cognee.modules.search.types import SearchType

        self._cognee = cognee
        self._SearchType = SearchType
        self._run = asyncio.run
        self._ds = lambda node_id: f"aegis_{node_id}".replace(" ", "_")

    def remember(self, node: ClinicalNode) -> None:
        self._run(self._cognee.remember(describe(node), dataset_name=self._ds(node.id)))

    def remember_text(self, text: str, source: str) -> None:
        self._run(self._cognee.remember(text, dataset_name=self._ds(f"note_{source}")))

    def recall(self, query: str):
        return self._run(
            self._cognee.recall(
                query_text=query,
                query_type=self._SearchType.GRAPH_COMPLETION,
                include_references=True,
            )
        )

    def improve(self, node_id: str) -> None:
        self._run(self._cognee.improve(dataset=self._ds(node_id)))

    def forget(self, node_id: str) -> list[str]:
        self._run(self._cognee.forget(dataset=self._ds(node_id)))
        return [node_id]

    def all_nodes(self):  # graph dump — wired in a later phase for the visualizer
        raise NotImplementedError

    def active(self):
        raise NotImplementedError


def get_memory() -> AegisMemory:
    backend = os.getenv("CANON_BACKEND", os.getenv("AEGIS_BACKEND", "mock")).lower()
    return CogneeMemory() if backend == "cognee" else MockMemory()
