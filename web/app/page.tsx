"use client";

import { useEffect, useState } from "react";
import { Loader2, ShieldPlus } from "lucide-react";
import {
  api,
  type Patient,
  type SourceDoc,
  type Med,
  type ReconcileAction,
  type Handoff as HandoffData,
  type Candidate,
} from "@/lib/api";
import { Hero } from "@/components/Hero";
import { AddRecords } from "@/components/AddRecords";
import { SourceDocs } from "@/components/SourceDocs";
import { Timeline } from "@/components/Timeline";
import { SafetyCheck } from "@/components/SafetyCheck";
import { Handoff } from "@/components/Handoff";
import { AskRecord } from "@/components/AskRecord";
import { Erase } from "@/components/Erase";

type State = {
  patient?: Patient;
  docs: SourceDoc[];
  meds: Med[];
  actions: ReconcileAction[];
  handoff?: HandoffData;
  candidates: Candidate[];
  def?: Candidate;
};

export default function Page() {
  const [s, setS] = useState<State>({ docs: [], meds: [], actions: [], candidates: [] });
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  async function load(initial = false) {
    try {
      const [patient, timeline, reconcile, handoff, candidates] = await Promise.all([
        api.patient(),
        api.timeline(),
        api.reconcile(),
        api.handoff(),
        api.candidates(),
      ]);
      setS({
        patient: patient.patient,
        docs: patient.documents,
        meds: timeline.medications,
        actions: reconcile.actions,
        handoff,
        candidates: candidates.candidates,
        def: candidates.default,
      });
      setStatus("ready");
    } catch {
      if (initial) setStatus("error");
    }
  }

  useEffect(() => {
    load(true);
  }, []);

  if (status === "error") {
    return (
      <main className="grid min-h-screen place-items-center px-6 text-center">
        <div className="max-w-md">
          <ShieldPlus className="mx-auto h-10 w-10 text-teal" />
          <h1 className="mt-4 text-2xl font-semibold">Backend not reachable</h1>
          <p className="mt-2 text-sm text-muted">
            Start the API, then reload:
          </p>
          <pre className="mt-3 rounded-lg border border-line bg-black/30 p-3 text-left font-mono text-xs text-teal">
            uvicorn server.app:app --port 8000
          </pre>
        </div>
      </main>
    );
  }

  if (status === "loading") {
    return (
      <main className="grid min-h-screen place-items-center">
        <Loader2 className="h-6 w-6 animate-spin text-teal" />
      </main>
    );
  }

  return (
    <main className="pb-8">
      <Hero patient={s.patient} />
      <AddRecords onChange={() => load(false)} />
      <SourceDocs docs={s.docs} />
      <Timeline meds={s.meds} actions={s.actions} />
      <SafetyCheck candidates={s.candidates} initial={s.def} />
      {s.handoff && <Handoff data={s.handoff} />}
      <AskRecord />
      <Erase />
    </main>
  );
}
