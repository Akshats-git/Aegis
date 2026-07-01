# Canon — pitch & strategy

## The strategic wedge
Everyone in this hackathon will build memory that **remembers** (the six examples on the
hackathon page). The research-certified *unsolved* problems in 2026 agent memory are about
memory that **forgets correctly and self-corrects** — "confidently wrong" staleness and
machine unlearning. Cognee is one of the only tools that natively does this (graph +
`improve()` edge re-weighting + `forget()`). So we build the thing the field calls
unsolved, that Cognee uniquely does, and that competitors will skip.

## The prior-art guardrail (why this is defensible)
Stateless docs-retrieval (Context7, Gemini Docs MCP, "Skills") already patches the
**public** half: injecting current library docs. It cannot touch the **private** half —
your team's own accumulated, self-contradicting decisions. That is the **moat**: a
codebase's `decision → superseded_by → current` chain lives in ADRs/PRs/Slack and no docs
server can model it. We lead with that moat; the removed-public-API demo is the relatable
hook.

## Judging-criteria map
| Criterion | Canon's answer |
|-----------|----------------|
| Best Use of Cognee | All four verbs; `forget()`/`improve()` are the core, not decoration; needs a graph (cascade-forget + edge re-weight) a vector store can't do. |
| Potential Impact | ~42% of AI snippets hallucinate; every dev using AI agents hits this. Makes the hackathon's own shipped integrations (Claude Code/Codex) better. |
| Creativity | Solves a problem the literature calls unsolved; counter-intuitive "forgetting is the feature." |
| Technical Excellence | Versioned graph modeling + MCP + real feedback loop. |
| UX | Zero-config: it's an MCP server in the agent the dev already uses. |
| Presentation | Before/after "reversed decision resurrected vs. retired" demo + live graph diff. |

## 1-week build plan
- **Day 1–2** Cognee quickstart (`COGNEE-35`); wire `CogneeMemory` in `canon/memory.py`.
  **Validate forget() cascade semantics on derived edges** — the one technical unknown.
- **Day 3–4** MCP server against a real coding agent; ingest 1 real repo's ADRs + 3 libs' changelogs.
- **Day 5** `improve()` feedback loop from test/review outcomes.
- **Day 6** Live graph-diff visualizer (before/after forget).
- **Day 7** Polish, record demo, write the Best-Blogs submission (extra prize).

## Scope discipline
Lock to ONE repo's decisions + 3 libraries. Depth beats breadth for judges. Mock backend
keeps the demo green even if Cognee wiring slips.

## Backups
- **Lethe** — GDPR right-to-be-forgotten compliance engine (strongest `forget()` story, drier demo).
- **Hindsight** — anti-amnesia brain for on-call engineers (closest to last year's winners).
