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
          eyebrow="Always current"
          title="Your medications, kept up to date"
          desc="When your records disagree, Aegis trusts the most recent one and quietly clears out medicines you've stopped — so your list is always accurate."
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
                        <AlertTriangle className="h-3.5 w-3.5" /> needs care with new medicines
                      </span>
                    )}
                    {m.forgotten && <Badge tone="danger">removed · out of date</Badge>}
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
              <span className="label text-teal">What we updated for you</span>
            </div>
            {actions.length === 0 && (
              <p className="text-sm text-muted">Everything looks up to date.</p>
            )}
            {actions.map((a) => (
              <div key={a.entity} className="space-y-3 text-sm">
                <p className="text-muted">
                  Your records disagreed about{" "}
                  <span className="font-medium text-ink capitalize">{a.entity}</span>, so we
                  used the most recent one:
                </p>
                {a.forgotten.map((f, i) => (
                  <div key={i} className="rounded-lg border border-danger/30 bg-danger/5 p-3">
                    <div className="text-xs text-danger">Removed — no longer taking</div>
                    <div className="mt-0.5 capitalize">{a.entity}</div>
                    <div className="text-xs text-muted">From: {f.source}</div>
                  </div>
                ))}
                <div className="rounded-lg border border-teal/30 bg-teal/5 p-3">
                  <div className="text-xs text-teal">Current</div>
                  <div className="mt-0.5 capitalize">
                    {a.entity} <span className="text-muted">· {a.kept_status}</span>
                  </div>
                  <div className="text-xs text-muted">From: {a.kept_source}</div>
                </div>
              </div>
            ))}
          </Card>
        </Reveal>
      </div>
    </section>
  );
}
