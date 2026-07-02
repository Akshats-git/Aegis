"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Trash2, Loader2, Check } from "lucide-react";
import { api } from "@/lib/api";
import { Card, Reveal, SectionTitle, Button } from "./ui";

export function Erase({ onErased }: { onErased?: () => void }) {
  const [state, setState] = useState<"idle" | "confirm" | "loading" | "done">("idle");

  async function doErase() {
    setState("loading");
    try {
      await api.erase();
    } finally {
      setState("done");
      if (onErased) setTimeout(onErased, 1600);
    }
  }

  return (
    <section>
      <Reveal>
        <SectionTitle
          eyebrow="Your data, your choice"
          title="Delete everything, anytime"
          desc="Your records belong to you. Remove them whenever you like. Nothing is left behind."
        />
      </Reveal>
      <Reveal>
        <Card className="border-danger/20">
          <AnimatePresence mode="wait">
            {state === "done" ? (
              <motion.div
                key="done"
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-3"
              >
                <div className="grid h-10 w-10 place-items-center rounded-full border border-rose/40 bg-rose/10">
                  <Check className="h-5 w-5 text-rose" />
                </div>
                <div>
                  <div className="font-semibold text-rose">Everything has been deleted</div>
                  <div className="text-sm text-muted">
                    Your records are permanently gone. Nothing was kept.
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div key="idle" className="flex flex-wrap items-center justify-between gap-4">
                <p className="max-w-xl text-sm text-muted">
                  This permanently removes your entire health record from Aegis. This cannot
                  be undone.
                </p>
                {state === "confirm" ? (
                  <div className="flex gap-2">
                    <Button tone="ghost" onClick={() => setState("idle")}>
                      Cancel
                    </Button>
                    <Button tone="danger" onClick={doErase} disabled={state !== "confirm"}>
                      Confirm erasure
                    </Button>
                  </div>
                ) : (
                  <Button tone="danger" onClick={() => setState("confirm")}>
                    {state === "loading" ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                    Erase this record
                  </Button>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </Reveal>

      <p className="mx-auto mt-16 max-w-2xl pb-16 text-center text-xs text-muted">
        Aegis helps you stay informed and safe. It does not replace professional medical
        advice. Always talk to your doctor before changing any medicine.
      </p>
    </section>
  );
}
