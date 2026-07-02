"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FilePlus2, Loader2, Sparkles, FlaskConical, Plus, Check } from "lucide-react";
import { api, type FactSummary } from "@/lib/api";
import { Card, Reveal, SectionTitle, Badge, Button } from "./ui";

const SAMPLE_NOTE = `Neurology note, 2026-05-20. Patient reports migraines. Currently taking
warfarin 5mg daily for atrial fibrillation. Allergic to sulfa drugs (rash).`;

export function AddRecords({ onChange }: { onChange: () => void }) {
  const [tab, setTab] = useState<"paste" | "manual">("paste");
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  // paste
  const [text, setText] = useState("");
  const [source, setSource] = useState("");
  const [extracted, setExtracted] = useState<FactSummary[] | null>(null);

  // manual
  const [kind, setKind] = useState("medication");
  const [form, setForm] = useState<Record<string, string>>({ status: "active" });

  function say(msg: string) {
    setFlash(msg);
    setTimeout(() => setFlash(null), 2600);
  }

  async function submitText() {
    if (!text.trim()) return;
    setBusy(true);
    setExtracted(null);
    try {
      const r = await api.addText(text, source || undefined);
      if (r.ok) {
        setExtracted(r.extracted ?? []);
        say(`Extracted ${r.count} fact(s) and added to the record.`);
        setText("");
        onChange();
      } else {
        say(r.error ?? "Extraction failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function submitManual() {
    setBusy(true);
    try {
      const r = await api.addManual(kind, form);
      if (r.ok) {
        say(`Added ${r.added?.label}.`);
        setForm({ status: "active" });
        onChange();
      } else {
        say(r.error ?? "Could not add.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function loadSample() {
    setBusy(true);
    try {
      await api.loadSample();
      setExtracted(null);
      say("Loaded a sample profile so you can explore.");
      onChange();
    } finally {
      setBusy(false);
    }
  }

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const inputCls =
    "w-full rounded-lg border border-line bg-black/20 px-3 py-2 text-sm outline-none focus:border-teal/50";

  return (
    <section className="mx-auto mt-24 max-w-6xl px-6">
      <Reveal>
        <SectionTitle
          eyebrow="Get started"
          title="Add your health records"
          desc="Paste anything from a doctor's note, discharge summary, or prescription. Aegis organizes it for you. You can also add a medicine yourself. Everything updates your profile right away."
        />
      </Reveal>

      <Reveal>
        <Card>
          <div className="mb-4 flex items-center gap-2">
            <button
              onClick={() => setTab("paste")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === "paste" ? "bg-teal/15 text-teal" : "text-muted hover:text-ink"
              }`}
            >
              <span className="inline-flex items-center gap-1.5"><Sparkles className="h-4 w-4" /> Paste a note</span>
            </button>
            <button
              onClick={() => setTab("manual")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === "manual" ? "bg-teal/15 text-teal" : "text-muted hover:text-ink"
              }`}
            >
              <span className="inline-flex items-center gap-1.5"><Plus className="h-4 w-4" /> Add manually</span>
            </button>
            <Button tone="ghost" className="ml-auto !px-3 !py-1.5" onClick={loadSample} disabled={busy}>
              <FlaskConical className="h-3.5 w-3.5" /> Load sample
            </Button>
          </div>

          {tab === "paste" ? (
            <div className="space-y-3">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder={SAMPLE_NOTE}
                rows={5}
                className={`${inputCls} resize-y font-mono text-xs leading-relaxed`}
              />
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="Source label (e.g. Neurology note 2026-05-20)"
                  className={inputCls}
                />
                <Button onClick={submitText} disabled={busy || !text.trim()} className="shrink-0">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FilePlus2 className="h-4 w-4" />}
                  Extract & add
                </Button>
                <Button
                  tone="ghost"
                  className="shrink-0"
                  onClick={() => setText(SAMPLE_NOTE)}
                  disabled={busy}
                >
                  Try sample
                </Button>
              </div>
              {extracted && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {extracted.length === 0 && <span className="text-sm text-muted">No facts found.</span>}
                  {extracted.map((f, i) => (
                    <Badge key={i} tone="teal">{f.kind}: {f.label}</Badge>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {["medication", "condition", "allergy"].map((k) => (
                  <button
                    key={k}
                    onClick={() => { setKind(k); setForm({ status: "active" }); }}
                    className={`rounded-lg border px-3 py-1.5 text-sm capitalize transition-colors ${
                      kind === k ? "border-teal/50 bg-teal/10 text-teal" : "border-line text-muted"
                    }`}
                  >
                    {k}
                  </button>
                ))}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {kind === "medication" && (
                  <>
                    <input className={inputCls} placeholder="Drug name (e.g. sertraline)" onChange={set("name")} />
                    <input className={inputCls} placeholder="Drug class (e.g. SSRI, MAOI, NSAID)" onChange={set("drug_class")} />
                    <input className={inputCls} placeholder="Dose (e.g. 50mg daily)" onChange={set("dose")} />
                    <select className={inputCls} value={form.status} onChange={set("status")}>
                      <option value="active">active</option>
                      <option value="discontinued">discontinued</option>
                    </select>
                  </>
                )}
                {kind === "condition" && (
                  <>
                    <input className={inputCls} placeholder="Condition (e.g. hypertension)" onChange={set("name")} />
                    <select className={inputCls} value={form.status} onChange={set("status")}>
                      <option value="active">active</option>
                      <option value="resolved">resolved</option>
                    </select>
                  </>
                )}
                {kind === "allergy" && (
                  <>
                    <input className={inputCls} placeholder="Substance (e.g. penicillin)" onChange={set("substance")} />
                    <input className={inputCls} placeholder="Reaction (e.g. hives)" onChange={set("reaction")} />
                  </>
                )}
              </div>
              <Button onClick={submitManual} disabled={busy}>
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                Add record
              </Button>
            </div>
          )}

          <AnimatePresence>
            {flash && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-teal/30 bg-teal/10 px-3 py-2 text-sm text-teal"
              >
                <Check className="h-4 w-4" /> {flash}
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </Reveal>
    </section>
  );
}
