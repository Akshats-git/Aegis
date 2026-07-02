"use client";

import { useEffect, useState } from "react";
import { api, type Med, type ReconcileAction } from "@/lib/api";
import { Timeline } from "@/components/Timeline";
import { EmptyState, PageLoader } from "@/components/EmptyState";

export default function MedicationsPage() {
  const [loading, setLoading] = useState(true);
  const [meds, setMeds] = useState<Med[]>([]);
  const [actions, setActions] = useState<ReconcileAction[]>([]);

  useEffect(() => {
    (async () => {
      const [t, r] = await Promise.all([api.timeline(), api.reconcile()]);
      setMeds(t.medications);
      setActions(r.actions);
    })().finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoader />;
  if (meds.length === 0)
    return (
      <EmptyState
        title="No medications yet"
        desc="Add a record with your medicines and Aegis will build your timeline and keep it up to date."
      />
    );
  return <Timeline meds={meds} actions={actions} />;
}
