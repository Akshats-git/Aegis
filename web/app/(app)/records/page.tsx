"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type SourceDoc } from "@/lib/api";
import { AddRecords } from "@/components/AddRecords";
import { SourceDocs } from "@/components/SourceDocs";

export default function RecordsPage() {
  const [docs, setDocs] = useState<SourceDoc[]>([]);

  const load = useCallback(async () => {
    try {
      const p = await api.patient();
      setDocs(p.documents);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-16">
      <AddRecords onChange={load} />
      {docs.length > 0 && <SourceDocs docs={docs} />}
    </div>
  );
}
