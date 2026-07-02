# Aegis — the memory that keeps your health record honest

> Built on open-source [Cognee](https://www.cognee.ai) for the WeMakeDevs × Cognee hackathon
> *"The Hangover Part AI: Where's My Context?"*

You are the only permanent medical record you have. Every doctor sees a fragment. **Aegis**
is the memory that remembers everything they don't — and **forgets what could kill you.**

Aegis turns a patient's scattered records (from every clinic, over a lifetime) into one
living, self-correcting clinical knowledge graph, and acts as a **safety layer**: it
retires discontinued medications and resolved conditions so no doctor — or AI — ever acts
on a stale, dangerous fact, and it catches dangerous drug interactions *before* they cause
harm, citing the exact source note for every warning.

Stale medical facts don't just annoy you — they hurt you: a discontinued drug still listed
"active", a new prescription that fatally interacts with something buried in a two-year-old
note. Ordinary storage can't fix that. **Forgetting the right things is a safety feature** —
and it's exactly what Cognee's graph memory is built to do.

## The four memory verbs, as patient safety

| Verb | In Aegis |
|------|----------|
| `remember()` | Ingest discharge summaries, specialist notes, med lists, labs → a temporal clinical graph. |
| `recall()`   | "What should a new doctor know?" / "Is drug X safe for me?" — answered with cited evidence. |
| `improve()`  | Each visit reconciles the record; patient-reported side effects sharpen future safety checks. |
| `forget()`   | Discontinued meds / resolved / corrected facts are retired so they can never mislead. **The safety hero.** |

## Status
- **Phases 1–5 (done):** clinical model + memory engine, synthetic patient + ingestion,
  reconciliation & forget engine, drug-interaction safety net, and the live "new doctor"
  recall experience — **validated end-to-end against the real Cognee engine** (all four
  verbs: remember · recall · improve · forget).
- Phase 6 (next): demo polish, visualization, blog, video.

## Architecture (how Cognee is used)
- **Cognee = the memory substrate.** One connected dataset per patient → high-quality
  `recall()` with cited evidence; `remember()` ingest; `improve()` enrichment; `forget()`
  for true **right-to-be-forgotten** erasure of the whole record.
- **Aegis reconciliation engine = the safety brain.** Deterministically decides the
  authoritative current picture and forgets stale facts — guaranteed, not left to an LLM —
  so the interaction safety check runs on a clean, trustworthy medication list.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python demo.py                             # offline demo, no keys needed
AEGIS_BACKEND=cognee python demo_live.py   # live, against real Cognee (needs .env key)
python -m aegis.visualize                  # the patient safety view (timeline + alert card)
```

### Web app
```bash
# 1) API backend (instant deterministic engine; set AEGIS_BACKEND=cognee for live Cognee)
uvicorn server.app:app --port 8000
# 2) Frontend (see web/README.md)
cd web && npm install && npm run dev        # http://localhost:3000
```

The real backend uses open-source, self-hosted Cognee with OpenAI for extraction +
embeddings (config in `.env`). This is a **Best Use of Open Source** entry: open Cognee +
open synthetic data + open drug-interaction data.

## Limitations (by design)
- **Synthetic data only.** No real patient data is used.
- **Decision-support, not diagnosis.** Aegis flags risks for a clinician to review; it does
  not prescribe or replace medical judgement.
- **Curated interaction set.** The demo ships a focused, open interaction knowledge base;
  the design scales to the live NIH RxNav / openFDA APIs.
- **Forgetting is split intentionally.** Cognee handles memory + true erasure; a
  deterministic engine handles safety-critical reconciliation, so the current picture is
  guaranteed rather than left to an LLM.

Licensed under the MIT License — see [LICENSE](LICENSE).

> ⚕️ Aegis is a patient-advocacy / decision-support prototype using synthetic data. It is
> not a medical device and does not replace professional medical judgement.
