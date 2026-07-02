"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ShieldAlert, ShieldCheck, Loader2, Stethoscope, FileWarning } from "lucide-react";
import { api, type Candidate, type SafetyResult } from "@/lib/api";
import { Card, Reveal, SectionTitle, Badge, Button } from "./ui";

export function SafetyCheck({
  candidates,
  initial,
}: {
  candidates: Candidate[];
  initial?: Candidate;
}) {
  const [selected, setSelected] = useState<Candidate>(initial ?? candidates[0]);
  const [result, setResult] = useState<SafetyResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function run(c: Candidate) {
    setSelected(c);
    setLoading(true);
    setResult(null);
    try {
      // small delay so the "checking" state reads on stage
      await new Promise((r) => setTimeout(r, 450));
      setResult(await api.safetyCheck(c.name, c.drug_class, c.indication));
    } finally {
      setLoading(false);
    }
  }

  const block = result?.verdict === "block";

  return (
    <section>
      <Reveal>
        <SectionTitle
          eyebrow="Peace of mind"
          title="Check a new medicine before you take it"
          desc="A doctor suggested something new? Check it here first. Aegis compares it against your current medicines and warns you if it isn't safe."
        />
      </Reveal>

      <div className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
        <Reveal>
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Stethoscope className="h-4 w-4 text-rose" />
              <span className="label">Pick a medicine to check</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {candidates.map((c) => (
                <button
                  key={c.name}
                  onClick={() => run(c)}
                  className={`rounded-xl border px-3 py-2 text-left text-sm transition-all ${
                    selected.name === c.name
                      ? "border-rose/50 bg-rose/10"
                      : "border-line bg-white/5 hover:bg-white/10"
                  }`}
                >
                  <div className="font-medium capitalize">{c.name}</div>
                  <div className="text-xs text-muted">for {c.indication}</div>
                </button>
              ))}
            </div>
            <Button className="mt-5 w-full" onClick={() => run(selected)} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Checking…
                </>
              ) : (
                <>Run safety check</>
              )}
            </Button>
          </Card>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="min-h-[220px]">
            <AnimatePresence mode="wait">
              {loading && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="grid h-full min-h-[220px] place-items-center rounded-2xl border border-line bg-panel"
                >
                  <div className="flex items-center gap-2 text-muted">
                    <Loader2 className="h-4 w-4 animate-spin" /> analyzing current record…
                  </div>
                </motion.div>
              )}

              {!loading && result && (
                <motion.div
                  key={result.proposed.name + result.verdict}
                  initial={{ opacity: 0, scale: 0.96, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                  className={`overflow-hidden rounded-2xl border p-6 ${
                    block
                      ? "border-danger/50 bg-danger/10"
                      : "border-rose/50 bg-rose/10"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {block ? (
                      <ShieldAlert className="h-8 w-8 text-danger" />
                    ) : (
                      <ShieldCheck className="h-8 w-8 text-rose" />
                    )}
                    <div>
                      <div className={`text-xl font-bold ${block ? "text-danger" : "text-rose"}`}>
                        {block ? "Not safe for you" : "Looks safe"}
                      </div>
                      <div className="text-sm capitalize text-muted">
                        {result.proposed.name}
                      </div>
                    </div>
                  </div>

                  {result.alerts.map((a, i) => (
                    <div key={i} className="mt-5 space-y-2 border-t border-line pt-4">
                      <div className="flex items-center gap-2 text-danger">
                        <FileWarning className="h-4 w-4" />
                        <span className="font-semibold">Risk: {a.effect}</span>
                      </div>
                      <div className="text-sm text-muted">
                        It can react badly with{" "}
                        <span className="font-medium text-ink">{a.conflicting_drug}</span>,
                        which you&apos;re currently taking.
                      </div>
                      <div className="rounded-lg border border-line bg-black/20 p-3 text-xs text-muted">
                        {a.management}
                      </div>
                      <div className="pt-1 text-xs text-muted">
                        Based on your record from{" "}
                        <span className="text-ink">{a.patient_source}</span>.
                      </div>
                    </div>
                  ))}

                  {block && result.alternatives.length > 0 && (
                    <div className="mt-4 border-t border-line pt-4">
                      <div className="mb-2 text-sm font-semibold text-rose">
                        Safer options to ask your doctor about
                      </div>
                      <ul className="space-y-1 text-sm text-muted">
                        {result.alternatives.map((alt) => (
                          <li key={alt}>• {alt}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              )}

              {!loading && !result && (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="grid h-full min-h-[220px] place-items-center rounded-2xl border border-dashed border-line text-sm text-muted"
                >
                  Select a drug and run the check.
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
