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
- **Phase 1 (done):** clinical data model + memory engine (mock + validated Cognee backend).
- Phase 2: synthetic patient + ingestion · Phase 3: reconciliation & forget engine ·
  Phase 4: drug-interaction safety net · Phase 5: recall & the "new doctor" experience ·
  Phase 6: demo & polish.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python demo.py                 # offline smoke demo, no keys needed
```

The real backend uses open-source, self-hosted Cognee with OpenAI for extraction +
embeddings (config in `.env`). This is a **Best Use of Open Source** entry: open Cognee +
open synthetic data + open drug-interaction data.

> ⚕️ Aegis is a patient-advocacy / decision-support prototype using synthetic data. It is
> not a medical device and does not replace professional medical judgement.

See [PITCH.md](PITCH.md) for the strategy and judging-criteria mapping.
