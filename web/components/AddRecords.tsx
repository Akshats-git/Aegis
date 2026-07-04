"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FilePlus2, Loader2, Sparkles, Plus, Check, X } from "lucide-react";
import { api } from "@/lib/api";
import { Card, Reveal, SectionTitle, Button } from "./ui";

type MedRow = { name: string; drug_class: string; dose: string };
type CondRow = { name: string };
type AllergyRow = { substance: string; reaction: string };

const emptyMed = (): MedRow => ({ name: "", drug_class: "", dose: "" });
const emptyCond = (): CondRow => ({ name: "" });
const emptyAllergy = (): AllergyRow => ({ substance: "", reaction: "" });

const inputCls =
  "w-full rounded-lg border border-line bg-field px-3 py-2 text-sm outline-none focus:border-rose/50";

export function AddRecords({ onChange }: { onChange: () => void }) {
  const [tab, setTab] = useState<"paste" | "manual">("paste");
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  // paste
  const [text, setText] = useState("");
  const [source, setSource] = useState("");

  // manual — fill medications, conditions and allergies together, like a real report
  const [meds, setMeds] = useState<MedRow[]>([emptyMed()]);
  const [conds, setConds] = useState<CondRow[]>([emptyCond()]);
  const [allergies, setAllergies] = useState<AllergyRow[]>([emptyAllergy()]);

  function say(msg: string) {
    setFlash(msg);
    setTimeout(() => setFlash(null), 2600);
  }

  async function submitText() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const r = await api.addText(text, source || undefined);
      if (r.ok) {
        say(`Added ${r.count} fact(s). See it below under “Every record, together.”`);
        setText("");
        setSource("");
        onChange();
      } else {
        say(r.error ?? "Extraction failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function submitManual() {
    const payload = {
      medications: meds.filter((m) => m.name.trim()),
      conditions: conds.filter((c) => c.name.trim()),
      allergies: allergies.filter((a) => a.substance.trim()),
    };
    const total =
      payload.medications.length + payload.conditions.length + payload.allergies.length;
    if (total === 0) {
      say("Add at least one medication, condition, or allergy.");
      return;
    }
    setBusy(true);
    try {
      const r = await api.addManualBatch(payload);
      if (r.ok) {
        say(`Added ${r.count} record(s) to your profile.`);
        setMeds([emptyMed()]);
        setConds([emptyCond()]);
        setAllergies([emptyAllergy()]);
        onChange();
      } else {
        say(r.error ?? "Could not add.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <Reveal>
        <SectionTitle
          eyebrow="Get started"
          title="Add your health records"
          desc="Paste anything from a doctor's note, discharge summary, or prescription. Aegis sorts it into your record. You can also add your medications, conditions, and allergies by hand."
        />
      </Reveal>

      <Reveal>
        <Card>
          <div className="mb-4 flex items-center gap-2">
            <button
              onClick={() => setTab("paste")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === "paste" ? "bg-rose/15 text-rose" : "text-muted hover:text-ink"
              }`}
            >
              <span className="inline-flex items-center gap-1.5"><Sparkles className="h-4 w-4" /> Paste a note</span>
            </button>
            <button
              onClick={() => setTab("manual")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === "manual" ? "bg-rose/15 text-rose" : "text-muted hover:text-ink"
              }`}
            >
              <span className="inline-flex items-center gap-1.5"><Plus className="h-4 w-4" /> Add manually</span>
            </button>
          </div>

          {tab === "paste" ? (
            <div className="space-y-3">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste a doctor's note, discharge summary, or prescription here."
                rows={5}
                className={`${inputCls} resize-y font-mono text-xs leading-relaxed`}
              />
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="Where is this from? (optional)"
                  className={inputCls}
                />
                <Button onClick={submitText} disabled={busy || !text.trim()} className="shrink-0">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FilePlus2 className="h-4 w-4" />}
                  Extract & add
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <p className="text-sm text-muted">
                Add everything from your report below. Leave any section you don&apos;t need empty.
              </p>

              {/* Medications */}
              <RecordSection
                title="Medications"
                addLabel="Add medication"
                onAdd={() => setMeds((r) => [...r, emptyMed()])}
              >
                {meds.map((m, i) => (
                  <Row key={i} onRemove={() => setMeds((r) => r.filter((_, j) => j !== i))}>
                    <input
                      className={inputCls} placeholder="Medicine name" value={m.name}
                      onChange={(e) => setMeds((r) => r.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))}
                    />
                    <input
                      className={inputCls} placeholder="Type of medicine (optional)" value={m.drug_class}
                      onChange={(e) => setMeds((r) => r.map((x, j) => (j === i ? { ...x, drug_class: e.target.value } : x)))}
                    />
                    <input
                      className={inputCls} placeholder="Dose (optional)" value={m.dose}
                      onChange={(e) => setMeds((r) => r.map((x, j) => (j === i ? { ...x, dose: e.target.value } : x)))}
                    />
                  </Row>
                ))}
              </RecordSection>

              {/* Conditions */}
              <RecordSection
                title="Conditions"
                addLabel="Add condition"
                onAdd={() => setConds((r) => [...r, emptyCond()])}
              >
                {conds.map((c, i) => (
                  <Row key={i} onRemove={() => setConds((r) => r.filter((_, j) => j !== i))}>
                    <input
                      className={`${inputCls} sm:col-span-2`} placeholder="Condition name" value={c.name}
                      onChange={(e) => setConds((r) => r.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))}
                    />
                  </Row>
                ))}
              </RecordSection>

              {/* Allergies */}
              <RecordSection
                title="Allergies"
                addLabel="Add allergy"
                onAdd={() => setAllergies((r) => [...r, emptyAllergy()])}
              >
                {allergies.map((a, i) => (
                  <Row key={i} onRemove={() => setAllergies((r) => r.filter((_, j) => j !== i))}>
                    <input
                      className={inputCls} placeholder="What you're allergic to" value={a.substance}
                      onChange={(e) => setAllergies((r) => r.map((x, j) => (j === i ? { ...x, substance: e.target.value } : x)))}
                    />
                    <input
                      className={inputCls} placeholder="Reaction (optional)" value={a.reaction}
                      onChange={(e) => setAllergies((r) => r.map((x, j) => (j === i ? { ...x, reaction: e.target.value } : x)))}
                    />
                  </Row>
                ))}
              </RecordSection>

              <Button onClick={submitManual} disabled={busy}>
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                Save records
              </Button>
            </div>
          )}

          <AnimatePresence>
            {flash && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-rose/30 bg-rose/10 px-3 py-2 text-sm text-rose"
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

function RecordSection({
  title,
  addLabel,
  onAdd,
  children,
}: {
  title: string;
  addLabel: string;
  onAdd: () => void;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      <div className="space-y-2">{children}</div>
      <button
        type="button"
        onClick={onAdd}
        className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-rose transition-opacity hover:opacity-80"
      >
        <Plus className="h-3.5 w-3.5" /> {addLabel}
      </button>
    </div>
  );
}

function Row({ children, onRemove }: { children: React.ReactNode; onRemove: () => void }) {
  return (
    <div className="flex items-start gap-2">
      <div className="grid flex-1 gap-2 sm:grid-cols-2">{children}</div>
      <button
        type="button"
        onClick={onRemove}
        aria-label="Remove"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-line text-muted transition-colors hover:bg-field hover:text-danger"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
