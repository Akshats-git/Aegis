"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type Note } from "@/lib/api";
import { AddRecords } from "@/components/AddRecords";
import { SourceDocs } from "@/components/SourceDocs";

export default function RecordsPage() {
  const [notes, setNotes] = useState<Note[]>([]);

  const load = useCallback(async () => {
    try {
      const r = await api.notes();
      setNotes(r.notes);
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
      {notes.length > 0 && <SourceDocs notes={notes} onChange={load} />}
    </div>
  );
}
