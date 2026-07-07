"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FileText, ChevronRight, Pencil, Trash2, Loader2, Check, X } from "lucide-react";
import { api, type Note, type FactSummary } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { Card, Reveal, SectionTitle } from "./ui";

function prettyName(f: string) {
  return f.replace(/\.md$/, "").replace(/^\d{4}-\d{2}-\d{2}_/, "").replace(/_/g, " ");
}

export function SourceDocs({ notes, onChange }: { notes: Note[]; onChange: () => void }) {
  const [open, setOpen] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  function startEdit(n: Note) {
    setEditing(n.id);
    setDraft(n.text);
    setOpen(n.id);
  }

  async function save(id: string) {
    if (!draft.trim()) return;
    setBusy(true);
    try {
      const r = await api.updateNote(id, draft);
      if (r.ok) {
        setEditing(null);
        onChange();
      } else {
        alert(r.error ?? "Could not save the note.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    setBusy(true);
    try {
      const r = await api.deleteNote(id);
      if (r.ok) {
        setOpen(null);
        setEditing(null);
        setConfirmDelete(null);
        onChange();
      } else {
        alert(r.error ?? "Could not delete the note.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <Reveal>
        <SectionTitle
          eyebrow="All in one place"
          title="Every record, together"
          desc="Your notes from different clinics, newest first. Tap any one to read it, see what was found in it, and edit it."
        />
      </Reveal>
      <div className="space-y-3">
        {notes.map((n, i) => {
          const isOpen = open === n.id;
          const isEditing = editing === n.id;
          const when = formatDateTime(n.created);
          return (
            <Reveal key={n.id} delay={i * 0.05}>
              <Card className="group flex flex-col transition-colors hover:border-rose/30">
                <button
                  className="flex w-full items-start gap-3 text-left"
                  onClick={() => setOpen(isOpen ? null : n.id)}
                >
                  <FileText className="mt-0.5 h-5 w-5 shrink-0 text-rose" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium capitalize">{prettyName(n.name)}</div>
                    {when && <div className="mt-0.5 font-mono text-xs text-muted">{when}</div>}
                  </div>
                  <ChevronRight className={`ml-auto mt-0.5 h-4 w-4 text-muted transition-transform ${isOpen ? "rotate-90" : ""}`} />
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      {/* Extracted, split into categories */}
                      {n.facts.length > 0 && (
                        <div className="mt-4 space-y-4">
                          <MedicationTable meds={n.facts.filter((f) => f.kind === "medication")} />
                          <TagList label="Conditions" items={n.facts.filter((f) => f.kind === "condition")} />
                          <TagList label="Allergies" items={n.facts.filter((f) => f.kind === "allergy")} />
                        </div>
                      )}

                      {/* The note itself, editable */}
                      <div className="mt-4">
                        <div className="mb-1.5 flex items-center justify-between">
                          <span className="label">Note</span>
                          {!isEditing && (
                            confirmDelete === n.id ? (
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted">Delete this note?</span>
                                <IconButton onClick={() => setConfirmDelete(null)} title="Keep note">
                                  Cancel
                                </IconButton>
                                <IconButton onClick={() => remove(n.id)} title="Confirm delete" danger>
                                  {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                                  Delete
                                </IconButton>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1">
                                <IconButton onClick={() => startEdit(n)} title="Edit note">
                                  <Pencil className="h-3.5 w-3.5" /> Edit
                                </IconButton>
                                <IconButton onClick={() => setConfirmDelete(n.id)} title="Delete note" danger>
                                  <Trash2 className="h-3.5 w-3.5" /> Delete
                                </IconButton>
                              </div>
                            )
                          )}
                        </div>

                        {isEditing ? (
                          <div className="space-y-2">
                            <textarea
                              value={draft}
                              onChange={(e) => setDraft(e.target.value)}
                              rows={6}
                              className="w-full resize-y rounded-lg border border-line bg-field p-3 font-mono text-[11px] leading-relaxed outline-none focus:border-rose/50"
                            />
                            <p className="text-xs text-muted">
                              Saving re-reads the note and updates the categories above.
                            </p>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => save(n.id)}
                                disabled={busy || !draft.trim()}
                                className="inline-flex items-center gap-1.5 rounded-lg bg-rose px-3 py-1.5 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
                              >
                                {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                                Save
                              </button>
                              <button
                                onClick={() => setEditing(null)}
                                disabled={busy}
                                className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:text-ink"
                              >
                                <X className="h-3.5 w-3.5" /> Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-line bg-field p-3 font-mono text-[11px] leading-relaxed text-muted">
                            {n.text}
                          </pre>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}

function MedicationTable({ meds }: { meds: FactSummary[] }) {
  if (meds.length === 0) return null;
  return (
    <div>
      <div className="label mb-1.5">Medications</div>
      <div className="overflow-hidden rounded-lg border border-line">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-field text-left text-xs text-muted">
              <th className="px-3 py-2 font-medium">Medication</th>
              <th className="px-3 py-2 font-medium">Dose</th>
            </tr>
          </thead>
          <tbody>
            {meds.map((m, i) => {
              const inactive = m.status === "discontinued";
              return (
                <tr key={i} className="border-t border-line">
                  <td className="px-3 py-2">
                    <span className={inactive ? "text-muted line-through" : ""}>{m.label}</span>
                    {m.drug_class && <span className="text-muted"> · {m.drug_class}</span>}
                    {inactive && <span className="text-muted"> · discontinued</span>}
                  </td>
                  <td className="px-3 py-2 text-muted">{m.dose || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TagList({ label, items }: { label: string; items: FactSummary[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <div className="label mb-1.5">{label}</div>
      <div className="flex flex-wrap gap-2">
        {items.map((f, i) => {
          const inactive = f.status === "resolved";
          return (
            <span
              key={i}
              className="rounded-md border border-line bg-field px-2.5 py-1 text-sm"
            >
              <span className={inactive ? "text-muted line-through" : ""}>{f.label}</span>
              {f.detail && <span className="text-muted"> · {f.detail}</span>}
              {inactive && <span className="text-muted"> · resolved</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function IconButton({
  children,
  onClick,
  title,
  danger = false,
}: {
  children: React.ReactNode;
  onClick: () => void;
  title: string;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-muted transition-colors hover:bg-field ${
        danger ? "hover:text-danger" : "hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}
