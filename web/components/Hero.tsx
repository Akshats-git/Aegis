"use client";

import { motion } from "framer-motion";
import { ShieldPlus, Github } from "lucide-react";
import type { Patient } from "@/lib/api";
import { Badge } from "./ui";

export function Hero({ patient }: { patient?: Patient }) {
  return (
    <header className="relative mx-auto max-w-6xl px-6 pt-12">
      <nav className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-xl border border-teal/30 bg-teal/10">
            <ShieldPlus className="h-5 w-5 text-teal" />
          </div>
          <span className="text-lg font-semibold tracking-tight">Aegis</span>
        </div>
        <div className="flex items-center gap-3 text-sm text-muted">
          <span className="hidden sm:inline">Built on open-source Cognee</span>
          <Github className="h-4 w-4" />
        </div>
      </nav>

      <div className="relative mt-16 overflow-hidden rounded-3xl border border-line bg-panel p-8 backdrop-blur-xl sm:p-12">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-teal/10 blur-3xl" />
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        >
          <Badge tone="teal">Patient-safety memory · prototype</Badge>
          <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-[1.1] tracking-tight sm:text-6xl">
            The memory that keeps your <span className="gradient-text">health record honest</span>.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted">
            You are the only permanent medical record you have. Every doctor sees a fragment.
            Aegis remembers everything they don&apos;t — and{" "}
            <span className="text-ink">forgets what could hurt you.</span>
          </p>
        </motion.div>

        {patient && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="mt-8 flex flex-wrap items-center gap-2"
          >
            <Badge tone="muted">Patient</Badge>
            <span className="font-medium">{patient.name}</span>
            <span className="text-muted">
              · {patient.age}{patient.sex} · MRN {patient.mrn}
            </span>
            <Badge className="ml-1">synthetic — no real data</Badge>
          </motion.div>
        )}
      </div>
    </header>
  );
}
