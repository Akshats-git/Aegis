"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Loader2, Quote } from "lucide-react";
import { api, type RecallResult } from "@/lib/api";
import { Card, Reveal, SectionTitle, Badge, Button } from "./ui";

const SUGGESTIONS = [
  "List the current medications and what to avoid prescribing.",
  "Is it safe to prescribe an SSRI?",
  "What antidepressant is the patient on now?",
];

export function AskRecord() {
  const [q, setQ] = useState(SUGGESTIONS[0]);
  const [res, setRes] = useState<RecallResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    setLoading(true);
    setRes(null);
    try {
      setRes(await api.recall(q));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto mt-24 max-w-6xl px-6">
      <Reveal>
        <SectionTitle
          eyebrow="recall() · natural language"
          title="Ask the record anything"
          desc="Cognee answers over the knowledge graph with cited evidence, so every claim is traceable."
        />
      </Reveal>
      <Reveal>
        <Card>
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="flex flex-1 items-center gap-2 rounded-xl border border-line bg-black/20 px-3">
              <Search className="h-4 w-4 text-muted" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && ask()}
                className="w-full bg-transparent py-3 text-sm outline-none placeholder:text-muted"
                placeholder="Ask about this patient's record…"
              />
            </div>
            <Button onClick={ask} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Ask"}
            </Button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setQ(s)}
                className="chip text-muted hover:text-ink"
              >
                {s}
              </button>
            ))}
          </div>

          {res && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-5 border-t border-line pt-5"
            >
              <div className="mb-2 flex items-center gap-2">
                <Quote className="h-4 w-4 text-teal" />
                <span className="label text-teal">Answer</span>
                <Badge tone="muted">engine: {res.engine}</Badge>
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{res.answer}</p>
              {res.evidence.length > 0 && (
                <div className="mt-4 space-y-2">
                  <div className="label">Cited evidence</div>
                  {res.evidence.map((e, i) => (
                    <div key={i} className="rounded-lg border border-line bg-black/20 p-3 text-xs">
                      <div className="text-muted">{e.text}</div>
                      <div className="mt-1 font-mono text-teal">↳ {e.source}</div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </Card>
      </Reveal>
    </section>
  );
}
