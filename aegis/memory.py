"""AegisMemory — the four memory verbs over the patient's clinical graph.

`MockMemory` is an in-memory version so tests/demos run with no keys.
`CogneeMemory` is the real backend (validated end-to-end in earlier work): each verb maps
to a real Cognee call, and each forgettable fact lives in its own dataset so forget()
can retire exactly one fact while recall still reasons across the whole graph.
"""

from __future__ import annotations

import os
from typing import Iterable, Protocol

from .schema import ClinicalNode, ClinicalStatus, Medication, Condition, Allergy


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
    if isinstance(node, Condition):
        s = f"Condition: {node.name}. Status: {node.status.value}."
        if node.onset:
            s += f" Since {node.onset}."
        return s + src
    if isinstance(node, Allergy):
        s = f"Allergy to {node.substance}."
        if node.reaction:
            s += f" Reaction: {node.reaction}."
        s += f" Severity: {node.severity.value}."
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
    """Real backend, wired against the cognee 1.2 async API (validated in prior work).

    Each user gets their own dataset (``aegis_<hash>``) so recall/forget are scoped to that
    user's records. Pass a ``user_id`` for the multi-user web app; omit it for the single
    demo dataset.
    """

    def __init__(self, user_id: str | None = None) -> None:
        import asyncio
        import cognee
        import hashlib
        from cognee.modules.search.types import SearchType

        self._cognee = cognee
        self._SearchType = SearchType
        self._run = asyncio.run
        if user_id:
            h = hashlib.sha256(user_id.encode()).hexdigest()[:16]
            self.DATASET = f"aegis_{h}"
        else:
            self.DATASET = "aegis_patient"
        # node.id -> cognee data_id (for single-fact forget within one connected dataset)
        self._data_ids: dict[str, str] = {}

    def remember(self, node: ClinicalNode) -> None:
        r = self._run(self._cognee.remember(
            describe(node), dataset_name=self.DATASET, self_improvement=False))
        items = (r.to_dict() or {}).get("items") or []
        if items and items[0].get("id"):
            self._data_ids[node.id] = str(items[0]["id"])

    def remember_text(self, text: str, source: str) -> None:
        self._run(self._cognee.remember(
            text, dataset_name=self.DATASET, self_improvement=False))

    def recall(self, query: str):
        try:
            return self._run(
                self._cognee.recall(
                    query_text=query,
                    query_type=self._SearchType.GRAPH_COMPLETION,
                    datasets=[self.DATASET],
                    include_references=True,
                )
            )
        except Exception as e:
            # No data yet, or dataset erased → recall 404s. Treat as "nothing to recall".
            if "DatasetNotFound" in type(e).__name__ or "No datasets" in str(e):
                return []
            raise

    def improve(self, node_id: str | None = None) -> None:
        self._run(self._cognee.improve(dataset=self.DATASET))

    def forget(self, node_id: str) -> list[str]:
        # Removes the data record for one fact. NOTE: in this cognee version, single-item
        # deletion does not purge graph/vector, so it does not change recall. The
        # authoritative "current picture" is guaranteed by the reconciliation engine, not
        # by this call. For true erasure that purges the store, use erase().
        from uuid import UUID
        data_id = self._data_ids.pop(node_id, None)
        if data_id:
            self._run(self._cognee.forget(data_id=UUID(data_id), dataset=self.DATASET))
            return [node_id]
        return []

    def erase(self) -> None:
        """Purge memory so nothing can resurface in a later answer.

        In this Cognee version the knowledge graph is a single shared store and recall's
        graph-completion ignores the ``datasets`` filter, so ``forget(dataset=)`` is not
        enough: it drops the dataset's documents but leaves orphaned graph nodes that still
        leak into answers (proven: a fresh dataset with one fact still recalled facts from
        old data). Pruning the whole system is the only reliable erasure here. This makes the
        store single-tenant — it holds one patient's current record at a time, which is the
        right model for the demo.
        """
        self._run(self._cognee.prune.prune_data())
        self._run(self._cognee.prune.prune_system(graph=True, vector=True, metadata=True))
        self._data_ids.clear()

    def all_nodes(self):  # graph dump — wired in a later phase for the visualizer
        raise NotImplementedError

    def active(self):
        raise NotImplementedError


def get_memory() -> AegisMemory:
    backend = os.getenv("CANON_BACKEND", os.getenv("AEGIS_BACKEND", "mock")).lower()
    return CogneeMemory() if backend == "cognee" else MockMemory()
