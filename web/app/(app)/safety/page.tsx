"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { SafetyCheck } from "@/components/SafetyCheck";
import { EmptyState, PageLoader } from "@/components/EmptyState";

export default function SafetyPage() {
  const [loading, setLoading] = useState(true);
  const [count, setCount] = useState(0);

  useEffect(() => {
    api.records()
      .then((recs) => setCount(recs.count))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoader />;
  if (count === 0)
    return (
      <EmptyState
        title="Add records to check safety"
        desc="Once your medicines are on file, you can check whether a new medicine is safe for you."
      />
    );
  return <SafetyCheck />;
}
