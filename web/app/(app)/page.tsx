"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { Pill, HeartPulse, ShieldAlert, ArrowRight } from "lucide-react";
import { api, type Handoff } from "@/lib/api";
import { EmptyState, PageLoader } from "@/components/EmptyState";

function Stat({ icon: Icon, value, label, tone = "rose" }: {
  icon: React.ComponentType<{ className?: string }>;
  value: number;
  label: string;
  tone?: "rose" | "warn";
}) {
  const tint = tone === "warn" && value > 0 ? "bg-warn/10 text-warn" : "bg-rose/10 text-rose";
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <div className={`grid h-10 w-10 place-items-center rounded-xl ${tint}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="text-3xl font-semibold tabular-nums">{value}</div>
      </div>
      <div className="mt-3 text-sm text-muted">{label}</div>
    </div>
  );
}

export default function Overview() {
  const { data: session } = useSession();
  const [handoff, setHandoff] = useState<Handoff | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const [greeting, setGreeting] = useState("Welcome back");

  useEffect(() => {
    const h = new Date().getHours();
    setGreeting(h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening");
    (async () => {
      const [hf, recs] = await Promise.all([api.handoff(), api.records()]);
      setHandoff(hf);
      setCount(recs.count);
    })().catch(() => setCount(0));
  }, []);

  const name = (session?.user?.name || "there").split(" ")[0];
  const meds = handoff?.medications ?? [];
  const allergies = handoff?.allergies ?? [];
  const summary =
    meds.length > 0
      ? `You have ${meds.length} ${meds.length === 1 ? "medicine" : "medicines"} on file. Aegis keeps them up to date and checks new ones for safety.`
      : "Your records are saved. Add your medicines to turn on safety checks.";

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative overflow-hidden rounded-3xl border border-line bg-panel p-8 sm:p-10"
      >
        <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-rose/10 blur-3xl" />
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          {greeting}, <span className="gradient-text">{name}</span>.
        </h1>
        <p className="mt-3 max-w-xl text-muted">{summary}</p>
      </motion.div>

      {count === null ? (
        <PageLoader />
      ) : count === 0 ? (
        <EmptyState
          title="Let's set up your health record"
          desc="Add your first record to see your medications, safety checks and a summary you can share with any doctor."
        />
      ) : (
        <>
          {/* Snapshot */}
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat icon={Pill} value={meds.length} label="Current medications" />
            <Stat icon={HeartPulse} value={handoff?.conditions.length ?? 0} label="Active conditions" />
            <Stat icon={ShieldAlert} value={allergies.length} label="Allergies" tone="warn" />
          </div>

          {/* Current medications */}
          <div className="card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold">Current medications</h2>
              <Link
                href="/medications"
                className="inline-flex items-center gap-1 text-sm text-rose transition-colors hover:text-rose/80"
              >
                Manage <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            {meds.length === 0 ? (
              <div className="rounded-xl border border-dashed border-line p-8 text-center text-sm text-muted">
                No medications on file yet.
              </div>
            ) : (
              <div className="space-y-2">
                {meds.map((m) => (
                  <div
                    key={m.name}
                    className="flex items-center gap-3 rounded-xl border border-line bg-field px-4 py-3"
                  >
                    <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-rose/10">
                      <Pill className="h-4 w-4 text-rose" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-medium capitalize">{m.name}</div>
                      {m.drug_class && <div className="text-xs text-muted">{m.drug_class}</div>}
                    </div>
                    {m.dose && <div className="shrink-0 text-sm text-muted">{m.dose}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Allergies */}
          {allergies.length > 0 && (
            <div className="card border-warn/30 p-6">
              <div className="mb-3 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-warn" />
                <h2 className="font-semibold">Allergies</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {allergies.map((a) => (
                  <span
                    key={a.substance}
                    className="chip border-warn/30 bg-warn/10 text-warn"
                  >
                    {a.substance}
                    {a.reaction ? ` · ${a.reaction}` : ""}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
