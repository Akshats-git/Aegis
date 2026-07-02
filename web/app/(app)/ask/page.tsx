"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AskRecord } from "@/components/AskRecord";
import { EmptyState, PageLoader } from "@/components/EmptyState";

export default function AskPage() {
  const [loading, setLoading] = useState(true);
  const [count, setCount] = useState(0);

  useEffect(() => {
    api.records().then((r) => setCount(r.count)).finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoader />;
  if (count === 0)
    return (
      <EmptyState
        title="Add records to ask questions"
        desc="Once you have records on file, you can ask questions and get answers based on them."
      />
    );
  return <AskRecord />;
}
