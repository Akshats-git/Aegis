"use client";

import { useCallback, useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { Loader2, ArrowUp } from "lucide-react";
import {
  api,
  setUserId,
  type SourceDoc,
  type Med,
  type ReconcileAction,
  type Handoff as HandoffData,
  type Candidate,
} from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import { Hero } from "@/components/Hero";
import { AddRecords } from "@/components/AddRecords";
import { SourceDocs } from "@/components/SourceDocs";
import { Timeline } from "@/components/Timeline";
import { SafetyCheck } from "@/components/SafetyCheck";
import { Handoff } from "@/components/Handoff";
import { AskRecord } from "@/components/AskRecord";
import { Erase } from "@/components/Erase";

type Data = {
  hasData: boolean;
  docs: SourceDoc[];
  meds: Med[];
  actions: ReconcileAction[];
  handoff?: HandoffData;
  candidates: Candidate[];
  def?: Candidate;
};

export default function Page() {
  const { data: session, status } = useSession();
  const [d, setD] = useState<Data>({ hasData: false, docs: [], meds: [], actions: [], candidates: [] });
  const [ready, setReady] = useState(false);

  const load = useCallback(async () => {
    try {
      const [patient, timeline, reconcile, handoff, candidates] = await Promise.all([
        api.patient(), api.timeline(), api.reconcile(), api.handoff(), api.candidates(),
      ]);
      setD({
        hasData: patient.has_data,
        docs: patient.documents,
        meds: timeline.medications,
        actions: reconcile.actions,
        handoff,
        candidates: candidates.candidates,
        def: candidates.default,
      });
    } finally {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    const uid = (session?.user as { id?: string } | undefined)?.id;
    if (uid) {
      setUserId(uid);
      load();
    }
  }, [session, load]);

  if (status === "loading") {
    return (
      <main className="grid min-h-screen place-items-center">
        <Loader2 className="h-6 w-6 animate-spin text-teal" />
      </main>
    );
  }

  if (status === "unauthenticated" || !session) {
    return <SignIn />;
  }

  return (
    <main className="pb-8">
      <Hero user={session.user ?? {}} onSignOut={() => signOut()} />
      <AddRecords onChange={load} />

      {!ready ? (
        <div className="grid place-items-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-teal" />
        </div>
      ) : d.hasData ? (
        <>
          <SourceDocs docs={d.docs} />
          <Timeline meds={d.meds} actions={d.actions} />
          <SafetyCheck candidates={d.candidates} initial={d.def} />
          {d.handoff && <Handoff data={d.handoff} />}
          <AskRecord />
          <Erase onErased={load} />
        </>
      ) : (
        <section className="mx-auto mt-16 max-w-6xl px-6">
          <div className="card flex flex-col items-center gap-3 p-12 text-center">
            <ArrowUp className="h-6 w-6 text-teal" />
            <h3 className="text-xl font-semibold">Add your first record to get started</h3>
            <p className="max-w-md text-sm text-muted">
              Once you add a record above, you&apos;ll see your medication timeline, instant
              safety checks and a summary you can share with any doctor.
            </p>
          </div>
        </section>
      )}
    </main>
  );
}
