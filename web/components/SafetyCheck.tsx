"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ShieldAlert, ShieldCheck, AlertTriangle, Loader2, Search, Pill } from "lucide-react";
import { api, type SafetyResult, type Concern } from "@/lib/api";
import { Card, Reveal, SectionTitle, Badge, Button } from "./ui";

function sevTone(s: Concern["severity"]): "danger" | "warn" | "muted" {
  if (s === "life-threatening" || s === "severe") return "danger";
  if (s === "moderate") return "warn";
  return "muted";
}

const VERDICT = {
  block: { label: "Not safe", icon: ShieldAlert, text: "text-danger", border: "border-danger/50 bg-danger/10" },
  caution: { label: "Use caution", icon: AlertTriangle, text: "text-warn", border: "border-warn/50 bg-warn/10" },
  ok: { label: "Looks safe", icon: ShieldCheck, text: "text-rose", border: "border-rose/50 bg-rose/10" },
} as const;

export function SafetyCheck() {
  const [name, setName] = useState("");
  const [result, setResult] = useState<SafetyResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function run(medicine: string) {
    const q = medicine.trim();
    if (!q) return;
    setName(q);
    setLoading(true);
    setResult(null);
    try {
      setResult(await api.safetyCheck(q));
    } finally {
      setLoading(false);
    }
  }

  const v = result ? VERDICT[result.verdict] : null;
  const ctx = result?.checked_against;

  return (
    <section>
      <Reveal>
        <SectionTitle
          eyebrow="Peace of mind"
          title="Check a new medicine before you take it"
          desc="Type any medicine your doctor is considering. Aegis checks it against your current medicines, conditions and allergies. It flags anything unsafe."
        />
      </Reveal>

      <div className="mx-auto max-w-xl space-y-6">
        <Reveal>
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Pill className="h-4 w-4 text-rose" />
              <span className="label">Medicine to check</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-line bg-field px-3">
              <Search className="h-4 w-4 shrink-0 text-muted" />
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && run(name)}
                placeholder="Type a medicine name"
                className="w-full bg-transparent py-3 text-sm outline-none placeholder:text-muted"
              />
            </div>
            <Button className="mt-3 w-full" onClick={() => run(name)} disabled={loading || !name.trim()}>
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Checking</> : "Check safety"}
            </Button>
          </Card>
        </Reveal>

        <AnimatePresence mode="wait">
          {loading && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid min-h-[200px] place-items-center rounded-2xl border border-line bg-panel"
            >
              <div className="flex items-center gap-2 text-muted">
                <Loader2 className="h-4 w-4 animate-spin" /> checking against your full record…
              </div>
            </motion.div>
          )}

          {!loading && result && v && (
            <motion.div
              key={result.proposed.name + result.verdict}
              initial={{ opacity: 0, scale: 0.97, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className={`rounded-2xl border p-6 ${v.border}`}
            >
              <div className="flex items-center gap-3">
                <v.icon className={`h-8 w-8 ${v.text}`} />
                <div>
                  <div className={`text-xl font-bold ${v.text}`}>{v.label}</div>
                  <div className="text-sm capitalize text-muted">{result.proposed.name}</div>
                </div>
              </div>

              {ctx && (
                <div className="mt-3 text-xs text-muted">
                  Checked against {ctx.medications} current medication
                  {ctx.medications === 1 ? "" : "s"}, {ctx.conditions} condition
                  {ctx.conditions === 1 ? "" : "s"} and {ctx.allergies} allerg
                  {ctx.allergies === 1 ? "y" : "ies"}.
                </div>
              )}

              {result.concerns.length === 0 ? (
                <p className="mt-5 border-t border-line pt-4 text-sm text-muted">
                  No interactions found with anything currently on your record. Always
                  confirm with your doctor or pharmacist.
                </p>
              ) : (
                <div className="mt-5 space-y-3 border-t border-line pt-4">
                  {result.concerns.map((c, i) => (
                    <div key={i} className="rounded-xl border border-line bg-field p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={sevTone(c.severity)}>{c.severity}</Badge>
                        <span className="font-medium">{c.title}</span>
                        <span className="ml-auto text-[11px] uppercase tracking-wide text-muted">
                          {c.source === "reference" ? "Known contraindication" : "AI-assessed"}
                        </span>
                      </div>
                      {c.detail && <p className="mt-2 text-sm text-muted">{c.detail}</p>}
                      {c.related_to && (
                        <p className="mt-1 text-xs text-muted">
                          Related to: <span className="text-ink">{c.related_to}</span>
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {result.alternatives.length > 0 && (
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
        </AnimatePresence>
      </div>
    </section>
  );
}
