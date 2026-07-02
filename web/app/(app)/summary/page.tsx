"use client";

import { useEffect, useState } from "react";
import { api, type Handoff as HandoffData } from "@/lib/api";
import { Handoff } from "@/components/Handoff";
import { EmptyState, PageLoader } from "@/components/EmptyState";

export default function SummaryPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<HandoffData | null>(null);

  useEffect(() => {
    api.handoff().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoader />;
  const empty =
    !data ||
    (data.conditions.length === 0 && data.medications.length === 0 && data.allergies.length === 0);
  if (empty)
    return (
      <EmptyState
        title="No summary yet"
        desc="Add your records and Aegis will prepare a clear summary you can share with any doctor."
      />
    );
  return <Handoff data={data!} />;
}
