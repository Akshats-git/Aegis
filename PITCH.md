# Aegis — pitch & strategy

## The one-liner
> You are the only permanent medical record you have. Every doctor sees a fragment. Aegis
> is the memory that remembers everything they don't — and forgets what could kill you.

## The wedge
Most memory projects (and the hackathon's own examples) showcase `remember()`/`recall()`.
The research-certified *unsolved* problem is **stale, confidently-wrong memory**. Aegis puts
that problem where the stakes are maximal — patient safety — where **forgetting is a
life-safety feature**, not a convenience. Cognee's graph + `forget()` + `improve()` is
uniquely suited, and no `remember()`-only competitor can match it.

## Why it's airtight
- **Data risk killed:** synthetic patient records (no privacy/IRB issues); scalable via
  Synthea. Drug-interaction checks use **open** data (RxNav / openFDA).
- **Credibility:** framed as patient-held decision-support that *flags for your doctor* and
  **cites the source document for every claim** (Cognee evidence references) → trust.
- **Not the common "health lane":** it's a reconciliation + safety graph, not a symptom bot.
- **Aimed at the MacBook:** open-source Cognee + open data + open-sourced Aegis =
  Best Use of Open Source.

## The demo that wins (≈90s, life-or-death)
Fragmented records with a planted danger (a discontinued MAOI still marked active; a buried
cardiology note). A naive view recommends a drug that causes serotonin syndrome / a
hypertensive crisis. Aegis has already `forget()`-retired the stale med, surfaces the fatal
interaction with the source note cited, blocks it, and suggests a safe alternative — then
`improve()` learns a newly reported side effect live.

## Judging-criteria map
Impact (life-or-death) · Creativity (forgetting as safety) · Technical Excellence (temporal
graph + reconciliation + live interaction checking) · Best Use of Cognee (all four verbs +
provenance) · UX (timeline + graph + one red/green safety card) · Presentation (the most
memorable demo in the room).

## Build phases
1. Clinical foundation (model + memory) — **done**
2. Synthetic patient + ingestion
3. Reconciliation & forget engine
4. Drug-interaction safety net
5. Recall & the "new doctor" experience
6. Demo & polish (viz, README, blog, video)
