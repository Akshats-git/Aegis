"""Graph schema for Canon.

Two node families share one graph so a coding agent gets a single source of truth:

  Decision  — a team/codebase choice that can be superseded over time (the MOAT;
              no public docs-MCP can model this because it is private & contradictory).
  Symbol    — a library API symbol with a version-scoped status (the relatable hook).

Edges:
  Decision --SUPERSEDED_BY--> Decision     (reversal chain; old end is forget()-able)
  Symbol   --REPLACED_BY-----> Symbol       (deprecation chain)
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Status(str, Enum):
    ACTIVE = "active"        # current canon — safe to recall to the agent
    SUPERSEDED = "superseded"  # reversed decision — forget() candidate
    DEPRECATED = "deprecated"  # API on the way out
    REMOVED = "removed"        # API gone — must be forgotten


class Decision(BaseModel):
    id: str
    topic: str                       # e.g. "state-management"
    statement: str                   # e.g. "Use Zustand for client state"
    status: Status = Status.ACTIVE
    source: str                      # e.g. "ADR-0007" or "PR #142"
    superseded_by: str | None = None
    weight: float = Field(default=1.0)  # bumped by improve(), decayed when contradicted


class Symbol(BaseModel):
    id: str
    library: str                     # e.g. "openai"
    name: str                        # e.g. "Completion.create"
    version_introduced: str
    version_removed: str | None = None
    status: Status = Status.ACTIVE
    replacement: str | None = None
    source: str                      # changelog / release-note reference
    weight: float = Field(default=1.0)
