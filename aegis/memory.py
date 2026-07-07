"""AegisMemory: the memory operations over a patient's clinical graph.

MockMemory is an in-memory backend so tests and demos run without API keys.
CogneeMemory is the real backend, validated against cognee 1.2.2.

Aegis is single-tenant by design. One shared dataset holds the record a given instance
manages. Reliable erasure depends on cognee.prune.prune_data() and prune_system(), which
are global in this version of Cognee and have no per-dataset or per-user scope (single-item
forget() does not purge the graph here; see forget() below). As a result one process cannot
safely host several independent tenants. Aegis is meant to be self-hosted per person: you
run your own instance for your own record, much like you would run your own password
manager.
"""

from __future__ import annotations

import os
import re
from typing import Protocol

from .schema import ClinicalNode, ClinicalStatus, Medication, Condition, Allergy


class AegisMemory(Protocol):
    def remember(self, node: ClinicalNode) -> None: ...
    def recall(self, query: str): ...
    def improve(self) -> None: ...
    def forget(self, node_id: str) -> list[str]: ...


def describe(node: ClinicalNode) -> str:
    """Render a clinical fact as a sentence so Cognee can extract entities and relations."""
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
    return f"{kind}: {body}.{src}"


class MockMemory:
    """Deterministic in-memory backend for offline demos and tests."""

    def __init__(self) -> None:
        self._nodes: dict[str, ClinicalNode] = {}

    def remember(self, node: ClinicalNode) -> None:
        self._nodes[node.id] = node

    def recall(self, query: str) -> list[ClinicalNode]:
        # Keyword match over active facts. Graph reasoning lives in CogneeMemory.
        q = query.lower()
        return [n for n in self._active()
                if any(q in str(v).lower() for v in n.model_dump().values())]

    def improve(self) -> None:
        # No enrichment step for the in-memory backend.
        pass

    def forget(self, node_id: str) -> list[str]:
        return [node_id] if self._nodes.pop(node_id, None) else []

    def _active(self) -> list[ClinicalNode]:
        return [n for n in self._nodes.values()
                if getattr(n, "status", ClinicalStatus.ACTIVE) == ClinicalStatus.ACTIVE]


class CogneeMemory:
    """Real backend, wired against the cognee 1.2 async API.

    Uses one fixed, shared dataset (``aegis_patient``). See the module docstring for why
    this is single-tenant by design.
    """

    DATASET = "aegis_patient"

    def __init__(self) -> None:
        import asyncio
        import cognee
        from cognee.modules.search.types import SearchType

        self._cognee = cognee
        self._SearchType = SearchType
        self._run = asyncio.run
        # node.id -> cognee data_id (for single-fact forget within the connected dataset)
        self._data_ids: dict[str, str] = {}

    def remember(self, node: ClinicalNode) -> None:
        r = self._run(self._cognee.remember(
            describe(node), dataset_name=self.DATASET, self_improvement=False))
        items = (r.to_dict() or {}).get("items") or []
        if items and items[0].get("id"):
            self._data_ids[node.id] = str(items[0]["id"])

    def recall(self, query: str, *, system_prompt: str | None = None):
        """Return a graph-grounded, cited answer. ``system_prompt`` overrides the default
        answer style. The safety check uses it to request a structured JSON assessment
        instead of prose, while still reasoning over the same live graph."""
        try:
            return self._run(
                self._cognee.recall(
                    query_text=query,
                    query_type=self._SearchType.GRAPH_COMPLETION,
                    datasets=[self.DATASET],
                    include_references=True,
                    system_prompt=system_prompt,
                )
            )
        except Exception as e:
            # No data yet, or the dataset was erased, so recall returns a 404. Treat that
            # as nothing to recall.
            if "DatasetNotFound" in type(e).__name__ or "No datasets" in str(e):
                return []
            raise

    def improve(self) -> None:
        self._run(self._cognee.improve(dataset=self.DATASET))

    def forget(self, node_id: str) -> list[str]:
        # Removes the data record for one fact. In this version of Cognee, single-item
        # deletion does not purge the graph or vector store, so it does not change recall.
        # The authoritative current picture is guaranteed by the reconciliation engine, not
        # by this call. For erasure that purges the store, use erase().
        from uuid import UUID
        data_id = self._data_ids.pop(node_id, None)
        if data_id:
            self._run(self._cognee.forget(data_id=UUID(data_id), dataset=self.DATASET))
            return [node_id]
        return []

    def erase(self) -> None:
        """Purge memory so nothing can resurface in a later answer.

        In this version of Cognee the knowledge graph is a single shared store, and
        recall's graph completion ignores the ``datasets`` filter. So ``forget(dataset=)``
        is not enough: it drops the dataset's documents but leaves orphaned graph nodes that
        still leak into answers. Testing confirmed that a fresh dataset holding one fact
        still recalled facts from old data. Pruning the whole system is the only reliable
        way to erase here, which is why the store holds one patient's current record at a
        time.
        """
        self._run(self._cognee.prune.prune_data())
        self._run(self._cognee.prune.prune_system(graph=True, vector=True, metadata=True))
        self._data_ids.clear()


def parse_recall_answer(raw: str) -> tuple[str, list[dict]]:
    """Split a Cognee ``recall()`` answer from its trailing ``Evidence:`` block (added by
    ``include_references=True``) into the clean answer text and a list of citations."""
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


def get_memory() -> AegisMemory:
    backend = os.getenv("CANON_BACKEND", os.getenv("AEGIS_BACKEND", "mock")).lower()
    return CogneeMemory() if backend == "cognee" else MockMemory()
