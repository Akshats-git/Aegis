"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FileText, ChevronRight } from "lucide-react";
import type { SourceDoc } from "@/lib/api";
import { Card, Reveal, SectionTitle } from "./ui";

function prettyName(f: string) {
  return f.replace(/\.md$/, "").replace(/^\d{4}-\d{2}-\d{2}_/, "").replace(/_/g, " ");
}
function dateOf(f: string) {
  const m = f.match(/^(\d{4}-\d{2}-\d{2})/);
  return m ? m[1] : "";
}

export function SourceDocs({ docs }: { docs: SourceDoc[] }) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <section>
      <Reveal>
        <SectionTitle
          eyebrow="All in one place"
          title="Every record, together"
          desc="Your notes from different clinics, gathered in one place. Tap any one to read it."
        />
      </Reveal>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {docs.map((d, i) => (
          <Reveal key={d.name} delay={i * 0.06}>
            <Card className="group flex h-full flex-col transition-colors hover:border-rose/30">
              <button className="flex w-full items-start gap-3 text-left" onClick={() => setOpen(open === d.name ? null : d.name)}>
                <FileText className="mt-0.5 h-5 w-5 shrink-0 text-rose" />
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium capitalize">{prettyName(d.name)}</div>
                  <div className="mt-0.5 font-mono text-xs text-muted">{dateOf(d.name)}</div>
                </div>
                <ChevronRight className={`ml-auto h-4 w-4 text-muted transition-transform ${open === d.name ? "rotate-90" : ""}`} />
              </button>
              <AnimatePresence initial={false}>
                {open === d.name && (
                  <motion.pre
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-line bg-black/30 p-3 font-mono text-[11px] leading-relaxed text-muted"
                  >
                    {d.text}
                  </motion.pre>
                )}
              </AnimatePresence>
            </Card>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
