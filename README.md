# Canon — the self-correcting source-of-truth memory for AI coding agents

> Built on [Cognee](https://www.cognee.ai) for the WeMakeDevs × Cognee hackathon
> *"The Hangover Part AI: Where's My Context?"*

AI coding agents are **confidently wrong**. They suggest deprecated library APIs that
were removed three versions ago, and — worse — they resurrect your team's *reversed*
decisions ("use Redux") long after you moved on ("we use Zustand now"). Studies put
hallucinations in ~42% of AI-generated snippets.

Stateless docs-retrieval (Context7, Gemini Docs MCP) patches the **public** half of this
problem. It cannot touch the **private** half: your team's own accumulated, self-
contradicting decisions. That requires *memory that forgets and corrects itself* — which
is exactly what Cognee's graph engine does and a vector store cannot.

**Canon** is a Cognee-backed knowledge graph of your project's canonical truth, exposed to
any coding agent over MCP. It tracks `decision → superseded_by → current`, reinforces what
held (`improve()`), and **retires what was reversed or removed (`forget()`)** so your agent
can never suggest it again.

## The four memory verbs, load-bearing — not decoration

| Verb | In Canon |
|------|----------|
| `remember()` | Ingest ADRs, PR discussions, changelogs → graph of decisions & API symbols with version/status. |
| `recall()`   | Agent asks "what's our current decision on X?" / "is this API valid?" → current canon + evidence. |
| `improve()`  | Outcomes (tests pass, decision upheld in review) re-weight edges so canon sharpens over time. |
| `forget()`   | A reversed decision or removed API is cascade-retired from the graph — the moat. |

## Architecture

```
ADRs / PRs / changelogs ──ingest──▶  Cognee graph  ◀──MCP──  Claude Code / Codex / Cursor
                                     (canon/memory.py)        (canon/mcp_server.py)
                                          ▲
                                   improve() / forget()
                                     (feedback loop)
```

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add LLM_API_KEY (OpenAI); embeddings + LLM use OpenAI

python demo.py                  # OFFLINE mock demo — no keys, always green
CANON_BACKEND=cognee python demo_live.py   # LIVE demo against the real Cognee engine
```

Two demos:
- **`demo.py`** — mock backend, no keys, always green (safe fallback for the stage).
- **`demo_live.py`** — real Cognee: `remember()` → `recall()` → `forget()`, and shows the
  superseded decision's evidence chunk **vanish** from the graph after `forget()`. ✅ validated.

`.env` uses OpenAI for both the graph-extraction LLM (`gpt-4o-mini`) and embeddings
(`text-embedding-3-small`). Self-hosted Cognee needs no Cognee Cloud key.

## Demo (the one that wins the room)
1. Naive RAG answer to "which state library do we use?" → **Redux** (it's mentioned most).
2. Canon answer → **Zustand**, with Redux shown `superseded_by` PR #142, retired via `forget()`.
3. Re-run after a dependency bump → a removed API vanishes from the graph live.

See [PITCH.md](PITCH.md) for the full strategy, judging-criteria mapping, and build plan.
# wemakedev
