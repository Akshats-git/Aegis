"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { Pill, HeartPulse, ShieldAlert, ShieldCheck, ClipboardList, MessageCircle, ArrowRight } from "lucide-react";
import { api, type Handoff } from "@/lib/api";
import { EmptyState, PageLoader } from "@/components/EmptyState";

function Stat({ icon: Icon, value, label }: {
  icon: React.ComponentType<{ className?: string }>;
  value: number;
  label: string;
}) {
  return (
    <div className="card p-5">
      <Icon className="h-5 w-5 text-rose" />
      <div className="mt-3 text-3xl font-semibold">{value}</div>
      <div className="text-sm text-muted">{label}</div>
    </div>
  );
}

const ACTIONS = [
  { href: "/safety", icon: ShieldCheck, title: "Check a medicine", desc: "See if a new medicine is safe for you." },
  { href: "/summary", icon: ClipboardList, title: "Doctor summary", desc: "Everything to share at your next visit." },
  { href: "/ask", icon: MessageCircle, title: "Ask Aegis", desc: "Get answers based on your records." },
];

export default function Overview() {
  const { data: session } = useSession();
  const [handoff, setHandoff] = useState<Handoff | null>(null);
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      const [h, recs] = await Promise.all([api.handoff(), api.records()]);
      setHandoff(h);
      setCount(recs.count);
    })().catch(() => setCount(0));
  }, []);

  const name = (session?.user?.name || "there").split(" ")[0];

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative overflow-hidden rounded-3xl border border-line bg-panel p-8 sm:p-10"
      >
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-rose/10 blur-3xl" />
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Welcome back, <span className="gradient-text">{name}</span>.
        </h1>
        <p className="mt-3 max-w-xl text-muted">
          Your records are kept in one place and always up to date. You&apos;ll be warned
          before a medicine could harm you.
        </p>
      </motion.div>

      {count === null ? (
        <PageLoader />
      ) : count === 0 ? (
        <EmptyState
          title="Let&apos;s set up your health record"
          desc="Add your first record to see your medications, safety checks and a summary you can share with any doctor."
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat icon={Pill} value={handoff?.medications.length ?? 0} label="Current medications" />
            <Stat icon={HeartPulse} value={handoff?.conditions.length ?? 0} label="Active conditions" />
            <Stat icon={ShieldAlert} value={handoff?.allergies.length ?? 0} label="Allergies" />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {ACTIONS.map(({ href, icon: Icon, title, desc }) => (
              <Link
                key={href}
                href={href}
                className="card group flex flex-col gap-3 p-5 transition-colors hover:border-rose/30"
              >
                <Icon className="h-5 w-5 text-rose" />
                <div>
                  <div className="font-medium">{title}</div>
                  <div className="mt-0.5 text-sm text-muted">{desc}</div>
                </div>
                <ArrowRight className="mt-auto h-4 w-4 text-muted transition-transform group-hover:translate-x-1" />
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
