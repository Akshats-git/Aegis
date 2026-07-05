# Aegis: the memory that keeps your health record honest

> Built on open-source [Cognee](https://www.cognee.ai) for the WeMakeDevs x Cognee hackathon.
> "The Hangover Part AI: Where's My Context?"

You are the only permanent medical record you have. Every doctor sees a fragment. Aegis is the memory that remembers everything they don't. It also forgets what could kill you.

Aegis turns a patient's scattered records (from every clinic, over a lifetime) into one living, self-correcting clinical knowledge graph. It acts as a safety layer. It retires discontinued medications and resolved conditions so no doctor, and no AI, ever acts on a stale, dangerous fact. It also catches dangerous drug interactions before they cause harm, and cites the exact source note for every warning. It ships as a real web app with login, your own record, and a red/green safety card. It is not just a CLI demo.

Stale medical facts don't just annoy you. They hurt you: a discontinued drug still listed as "active", or a new prescription that fatally interacts with something buried in a two-year-old note. Ordinary storage can't fix that. Forgetting the right things is a safety feature, and it's exactly what Cognee's graph memory is built to do.

## The four memory verbs, as patient safety, and where each lives in the product

| Verb | In Aegis | Where |
|------|----------|-------|
| `remember()` | Every note, medication, condition, and allergy is ingested into one connected graph. | Runs in the background on every record change (`server/cognee_bridge.py:resync`). |
| `forget()`   | When two records disagree (an old list says a drug is active, a newer note says it was stopped), the stale one gets a real, per-fact `forget()` call. Single-item `forget()` doesn't purge the graph or vector store in this Cognee version, so we don't stop there. The graph is then rebuilt from just the reconciled, current picture. This way a forgotten fact is guaranteed to never resurface in an answer, not just probably gone. | `resync`, triggered by reconciliation. |
| `recall()`   | Powers "Ask Aegis" (questions like "What should a new doctor know?" or "Is X safe for me?") with cited evidence. It also powers the safety check's broad, graph-grounded assessment, using the same `recall()` pipeline but with a custom prompt that asks for a structured verdict instead of prose. | `/api/recall`, `/api/safety-check` |
| `improve()`  | Runs after every sync so the graph keeps enriching as the record grows. | `resync` |
| `forget()` (dataset-level) | Right to be forgotten. Deleting your account purges the entire memory graph, provably: `recall()` afterwards finds nothing. | `/api/erase` |

The safety check layers a deterministic, guaranteed rule engine (the known life-threatening interactions, never left to an LLM) underneath the Cognee-grounded broad assessment. This means an AI false negative can never let a genuinely dangerous drug through, and an AI false positive can never block a genuinely safe one.

## Architecture: a deliberately single-tenant design

Aegis is self-hosted per person. You run your own instance for your own record, the same way you'd run your own password manager, not a multi-patient SaaS on shared infra. The Cognee-backed memory graph is a single shared graph for the record this instance manages.

This isn't a corner cut for the hackathon. `cognee.prune.prune_data()` and `prune_system()`, which is what real erasure needs since single-item `forget()` doesn't reliably purge the graph in this Cognee version, are global operations with no dataset or user scope in cognee 1.2.2. A single Cognee process genuinely can't host multiple independent tenants safely yet. Single-tenant, self-hosted is the honest, correct model given that, and it fits the product's own pitch: this is your memory, not a hospital's database.

The deterministic JSON record (your documents and structured facts) is isolated per signed-in account, since that part doesn't touch Cognee's shared state. Multi-tenant Cognee memory, once the underlying library supports scoped erasure, is the natural next step.

### Tech stack

| Layer | Tech | Notes |
|---|---|---|
| Frontend | Next.js 14, React 18, TypeScript | App Router, Tailwind CSS, Framer Motion, NextAuth (Google + guest login) |
| Backend | FastAPI, Uvicorn | Own email/password auth (PBKDF2-HMAC-SHA256), no extra dependency |
| Storage | JSON on disk | One file per account, keyed by user id |
| Memory | Cognee (self-hosted) | Graph memory: remember, forget, recall, improve |
| LLM | OpenAI | Used by Cognee for extraction and embeddings; swappable in `.env` |
| Safety rules | Plain Python | Deterministic drug-interaction checks, not AI-decided |
| Data | Synthetic only | No real patient data |

### Where things live

| Folder | What's in it |
|---|---|
| `web/` | The Next.js app (UI, login, forms, timeline) |
| `server/app.py` | The API the frontend talks to |
| `server/auth.py` | Sign up / login |
| `server/store.py` | Reads and writes each account's record |
| `server/cognee_bridge.py` | The only file that talks to Cognee |
| `server/safety.py` | The hard-coded drug-interaction rules |
| `aegis/` | Clinical data model, note parsing, reconciliation, interaction data, reports |

## Status
All phases are done and validated live against real Cognee:
- Clinical model, reconciliation and forget engine, drug-interaction safety net.
- A full web product: FastAPI backend, Next.js frontend, Google/Guest sign-in, per-account
  records, add-by-note or by-form, a timeline, a doctor handoff summary, and the
  interactive safety check.
- Cognee wired into three live features, not a side demo: "Ask Aegis" recall, the safety
  check's broad assessment, and account erasure. See the table above.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY (OpenAI), see below
python demo.py         # offline demo, no keys needed
python demo_live.py    # live, against real Cognee, the flagship demo (needs .env key)
python -m aegis.visualize   # terminal timeline + alert card view
```

### Web app
```bash
# 1) API backend
uvicorn server.app:app --port 8000
# 2) Frontend (see web/README.md)
cd web && npm install && npm run dev        # http://localhost:3000
```

The real backend uses open-source, self-hosted Cognee with OpenAI for extraction and
embeddings (config in `.env`). This is a Best Use of Open Source entry: open Cognee,
open synthetic data, and open drug-interaction data.

## Limitations (by design)
- Synthetic data only. No real patient data is used.
- Decision-support, not diagnosis. Aegis flags risks for a clinician to review; it does
  not prescribe or replace medical judgement.
- Curated interaction set. The demo ships a focused, open interaction knowledge base;
  the design scales to the live NIH RxNav / openFDA APIs.
- Single-tenant memory, per instance. See Architecture above. This is a deliberate
  consequence of how erasure works in this Cognee version, not an oversight.
- The safety-critical "block" verdict is never AI-decided. It only ever comes from the
  deterministic reference rules. Cognee's graph-grounded assessment can add caution-level
  concerns but can't override a rule, and can't be talked out of one either.

Licensed under the MIT License. See [LICENSE](LICENSE).

> Aegis is a patient-advocacy / decision-support prototype using synthetic data. It is
> not a medical device and does not replace professional medical judgement.

---

Built with the help of [Claude](https://claude.com/claude-code).
