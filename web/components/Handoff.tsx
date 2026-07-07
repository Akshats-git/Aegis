"use client";

import { useState } from "react";
import {
  HeartPulse, Pill, ShieldAlert, Clock, AlertTriangle, Copy, Check, Stethoscope,
} from "lucide-react";
import type { Handoff as HandoffData } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Card, Reveal, SectionTitle, Badge } from "./ui";

const SEV_ORDER: Record<string, number> = {
  "life-threatening": 0, severe: 1, moderate: 2, mild: 3,
};

function sevTone(s: string): "danger" | "warn" | "muted" {
  if (s === "life-threatening" || s === "severe") return "danger";
  if (s === "moderate") return "warn";
  return "muted";
}

// Medicines that need active caution when a clinician prescribes something new.
function medCaution(drugClass: string | null): string | null {
  if (drugClass === "MAOI")
    return "Interaction risk: avoid triptans, SSRIs/SNRIs, opioids like tramadol/meperidine, and decongestants. Needs a 14-day washout after stopping.";
  if (drugClass === "anticoagulant")
    return "Bleeding risk: use caution with NSAIDs and other anticoagulants.";
  return null;
}

export function Handoff({ data }: { data: HandoffData }) {
  const [copied, setCopied] = useState(false);

  const allergies = [...data.allergies].sort(
    (a, b) => (SEV_ORDER[a.severity] ?? 4) - (SEV_ORDER[b.severity] ?? 4),
  );
  const criticalAllergies = allergies.filter(
    (a) => a.severity === "life-threatening" || a.severity === "severe",
  );
  const cautionMeds = data.medications.filter((m) => medCaution(m.drug_class));
  const hasFlags = criticalAllergies.length > 0 || cautionMeds.length > 0;

  async function copy() {
    try {
      await navigator.clipboard.writeText(data.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <section className="space-y-6">
      <Reveal>
        <SectionTitle
          eyebrow="For your care team"
          title="Emergency-ready summary"
          desc="The essentials a clinician needs before treating you: allergies, current medicines, active conditions, and what was recently stopped. Reconciled from your records and kept up to date."
        />
      </Reveal>

      {/* Critical flags: the first thing an emergency clinician should see */}
      <Reveal>
        <div
          className={`rounded-2xl border p-6 ${
            hasFlags ? "border-danger/50 bg-danger/10" : "border-rose/40 bg-rose/5"
          }`}
        >
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle className={`h-5 w-5 ${hasFlags ? "text-danger" : "text-rose"}`} />
            <span className={`text-sm font-semibold ${hasFlags ? "text-danger" : "text-rose"}`}>
              {hasFlags ? "Critical flags: read first" : "No critical flags on record"}
            </span>
          </div>
          {hasFlags ? (
            <ul className="space-y-2.5 text-sm">
              {criticalAllergies.map((a) => (
                <li key={a.substance} className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold capitalize text-danger">
                    Allergy: {a.substance}
                  </span>
                  <Badge tone="danger">{a.severity}</Badge>
                  {a.reaction && <span className="text-muted">{a.reaction}</span>}
                </li>
              ))}
              {cautionMeds.map((m) => (
                <li key={m.name} className="flex flex-col gap-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold capitalize text-danger">{m.name}</span>
                    <Badge tone="danger">{m.drug_class}</Badge>
                  </span>
                  <span className="text-xs leading-relaxed text-muted">
                    {medCaution(m.drug_class)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">
              No life-threatening allergies or high-interaction medicines are on file.
            </p>
          )}
        </div>
      </Reveal>

      {/* Full detail, laid out clearly */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Reveal>
          <SummaryCard icon={ShieldAlert} tone="danger" title="Allergies" count={allergies.length}>
            {allergies.length === 0 ? (
              <Empty>No known allergies on record.</Empty>
            ) : (
              allergies.map((a) => (
                <Item
                  key={a.substance}
                  title={a.substance}
                  badge={<Badge tone={sevTone(a.severity)}>{a.severity}</Badge>}
                  sub={a.reaction ? `Reaction: ${a.reaction}` : undefined}
                />
              ))
            )}
          </SummaryCard>
        </Reveal>

        <Reveal delay={0.05}>
          <SummaryCard icon={Pill} tone="rose" title="Current medications" count={data.medications.length}>
            {data.medications.length === 0 ? (
              <Empty>No current medications on record.</Empty>
            ) : (
              data.medications.map((m) => {
                const caution = medCaution(m.drug_class);
                const sub = [m.dose, m.started ? `since ${formatDate(m.started)}` : null]
                  .filter(Boolean)
                  .join(" · ");
                return (
                  <Item
                    key={m.name}
                    title={m.name}
                    badge={
                      m.drug_class ? (
                        <Badge tone={caution ? "danger" : "muted"}>{m.drug_class}</Badge>
                      ) : undefined
                    }
                    sub={sub || undefined}
                    warn={caution || undefined}
                  />
                );
              })
            )}
          </SummaryCard>
        </Reveal>

        <Reveal delay={0.1}>
          <SummaryCard icon={HeartPulse} tone="rose" title="Active conditions" count={data.conditions.length}>
            {data.conditions.length === 0 ? (
              <Empty>No active conditions on record.</Empty>
            ) : (
              data.conditions.map((c) => (
                <Item
                  key={c.name}
                  title={c.name}
                  sub={c.onset ? `since ${formatDate(c.onset)}` : undefined}
                />
              ))
            )}
          </SummaryCard>
        </Reveal>

        <Reveal delay={0.15}>
          <SummaryCard icon={Clock} tone="muted" title="Recently discontinued" count={data.discontinued.length}>
            {data.discontinued.length === 0 ? (
              <Empty>Nothing recently discontinued.</Empty>
            ) : (
              <>
                <p className="mb-1 text-xs text-muted">
                  Still relevant for drug interactions and washout windows.
                </p>
                {data.discontinued.map((d) => (
                  <Item
                    key={d.name}
                    title={d.name}
                    sub={
                      [d.stopped ? `stopped ${formatDate(d.stopped)}` : null, d.reason]
                        .filter(Boolean)
                        .join(" · ") || undefined
                    }
                  />
                ))}
              </>
            )}
          </SummaryCard>
        </Reveal>
      </div>

      {/* Share */}
      <Reveal>
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-line bg-panel p-5">
          <div className="flex items-center gap-2 text-sm text-muted">
            <Stethoscope className="h-4 w-4 shrink-0 text-rose" />
            Hand this to a clinician or paste it straight into your chart.
          </div>
          <button
            onClick={copy}
            className="inline-flex items-center gap-2 rounded-xl bg-rose px-4 py-2.5 text-sm font-semibold text-black transition-opacity hover:opacity-90"
          >
            {copied ? (
              <><Check className="h-4 w-4" /> Copied</>
            ) : (
              <><Copy className="h-4 w-4" /> Copy summary</>
            )}
          </button>
        </div>
      </Reveal>

      <p className="pb-8 text-center text-xs text-muted">
        Prepared from your reconciled records. Decision support only, not a substitute for
        professional medical judgement.
      </p>
    </section>
  );
}

function SummaryCard({
  icon: Icon,
  tone,
  title,
  count,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  tone: "danger" | "rose" | "warn" | "muted";
  title: string;
  count: number;
  children: React.ReactNode;
}) {
  const tint = {
    danger: "bg-danger/10 text-danger",
    rose: "bg-rose/10 text-rose",
    warn: "bg-warn/10 text-warn",
    muted: "bg-field text-muted",
  }[tone];
  return (
    <Card className="h-full">
      <div className="mb-4 flex items-center gap-3">
        <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${tint}`}>
          <Icon className="h-5 w-5" />
        </div>
        <h3 className="font-semibold">{title}</h3>
        <span className="ml-auto text-sm tabular-nums text-muted">{count}</span>
      </div>
      <div className="space-y-2.5">{children}</div>
    </Card>
  );
}

function Item({
  title,
  badge,
  sub,
  warn,
}: {
  title: string;
  badge?: React.ReactNode;
  sub?: string;
  warn?: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-field p-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium capitalize">{title}</span>
        {badge}
      </div>
      {sub && <div className="mt-1 text-sm text-muted">{sub}</div>}
      {warn && (
        <div className="mt-2 flex items-start gap-1.5 rounded-lg bg-danger/10 px-2.5 py-1.5 text-xs text-danger">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span className="leading-relaxed">{warn}</span>
        </div>
      )}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-xl border border-dashed border-line p-4 text-sm text-muted">
      {children}
    </p>
  );
}
