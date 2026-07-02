"use client";

import { motion } from "framer-motion";
import { ShieldPlus, HeartPulse } from "lucide-react";
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
        <div className="hidden items-center gap-2 text-sm text-muted sm:flex">
          <HeartPulse className="h-4 w-4 text-teal" />
          <span>Your health, remembered safely</span>
        </div>
      </nav>

      <div className="relative mt-16 overflow-hidden rounded-3xl border border-line bg-panel p-8 backdrop-blur-xl sm:p-12">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-teal/10 blur-3xl" />
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        >
          <Badge tone="teal">A safer way to carry your health history</Badge>
          <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-[1.1] tracking-tight sm:text-6xl">
            Never repeat your <span className="gradient-text">medical history</span> again.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted">
            Aegis keeps all your health records in one place, always up to date — so any new
            doctor instantly knows what matters, and{" "}
            <span className="text-ink">you&apos;re warned before a medicine could harm you.</span>
          </p>
        </motion.div>

        {patient && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="mt-8 flex flex-wrap items-center gap-3 rounded-2xl border border-line bg-black/20 px-4 py-3"
          >
            <div className="grid h-10 w-10 place-items-center rounded-full bg-teal/10 text-sm font-semibold text-teal">
              {patient.name.split(" ").map((p) => p[0]).join("")}
            </div>
            <div>
              <div className="font-medium">{patient.name}</div>
              <div className="text-sm text-muted">{patient.age} years · {patient.sex}</div>
            </div>
            <Badge className="ml-auto" tone="muted">Sample profile</Badge>
          </motion.div>
        )}
      </div>
    </header>
  );
}
