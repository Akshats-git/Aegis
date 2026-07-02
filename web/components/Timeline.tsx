"use client";

import { motion } from "framer-motion";
import { Pill, AlertTriangle, Sparkles } from "lucide-react";
import type { Med, ReconcileAction } from "@/lib/api";
import { Card, Reveal, SectionTitle, Badge } from "./ui";

function classTone(c: string | null) {
  return c === "MAOI" ? "text-danger" : "text-teal";
}

export function Timeline({
  meds,
  actions,
}: {
  meds: Med[];
  actions: ReconcileAction[];
}) {
  return (
    <section className="mx-auto mt-24 max-w-6xl px-6">
      <Reveal>
        <SectionTitle
          eyebrow="remember() + forget()"
          title="One honest, self-correcting picture"
          desc="Aegis reconciles conflicting records: the most recent note wins, and stale facts are forgotten so they can never mislead the next decision."
        />
      </Reveal>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Reveal>
          <Card>
            <div className="label mb-4">Medication timeline</div>
            <ol className="relative space-y-3 border-l border-line pl-6">
              {meds.map((m, i) => (
                <motion.li
                  key={m.id}
                  initial={{ opacity: 0, x: -8 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.07 }}
                  className="relative"
                >
                  <span
                    className={`absolute -left-[27px] top-1.5 h-3 w-3 rounded-full border-2 ${
                      m.status === "active"
                        ? m.danger
                          ? "border-danger bg-danger"
                          : "border-teal bg-teal"
                        : "border-muted bg-bg"
                    }`}
                  />
                  <div
                    className={`flex items-center gap-2 ${
                      m.forgotten ? "opacity-45" : ""
                    }`}
                  >
                    <Pill className={`h-4 w-4 ${classTone(m.drug_class)}`} />
                    <span
                      className={`font-medium ${
                        m.forgotten ? "line-through decoration-danger/70" : ""
                      }`}
                    >
                      {m.name}
                    </span>
                    <Badge tone="muted">{m.drug_class}</Badge>
                    {m.status === "active" ? (
                      <Badge tone={m.danger ? "danger" : "teal"}>active</Badge>
                    ) : (
                      <Badge tone="muted">{m.status}</Badge>
                    )}
                    {m.danger && (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-danger">
                        <AlertTriangle className="h-3.5 w-3.5" /> MAOI
                      </span>
                    )}
                    {m.forgotten && <Badge tone="danger">✗ forgotten (stale)</Badge>}
                  </div>
                  <div className="mt-0.5 pl-6 font-mono text-xs text-muted">
                    {m.started ?? "?"} → {m.stopped ?? "present"} · {m.source}
                  </div>
                </motion.li>
              ))}
            </ol>
          </Card>
        </Reveal>

        <Reveal delay={0.1}>
          <Card className="h-full border-teal/20">
            <div className="mb-3 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-teal" />
              <span className="label text-teal">Reconciliation</span>
            </div>
            {actions.length === 0 && (
              <p className="text-sm text-muted">No conflicts detected.</p>
            )}
            {actions.map((a) => (
              <div key={a.entity} className="space-y-3 text-sm">
                <p className="text-muted">
                  Conflicting records for{" "}
                  <span className="font-medium text-ink capitalize">{a.entity}</span>:
                </p>
                {a.forgotten.map((f, i) => (
                  <div key={i} className="rounded-lg border border-danger/30 bg-danger/5 p-3">
                    <div className="text-xs text-danger">✗ forgotten</div>
                    <div className="mt-0.5">
                      {a.entity} <span className="text-muted">[{f.status}]</span>
                    </div>
                    <div className="font-mono text-xs text-muted">{f.source}</div>
                  </div>
                ))}
                <div className="rounded-lg border border-teal/30 bg-teal/5 p-3">
                  <div className="text-xs text-teal">✓ kept (most recent)</div>
                  <div className="mt-0.5">
                    {a.entity} <span className="text-muted">[{a.kept_status}]</span>
                  </div>
                  <div className="font-mono text-xs text-muted">{a.kept_source}</div>
                </div>
              </div>
            ))}
          </Card>
        </Reveal>
      </div>
    </section>
  );
}
