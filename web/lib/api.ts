// Typed client for the Aegis API. In the browser we call same-origin /api/* which Next
// rewrites to the FastAPI backend (see next.config.mjs).

export type Med = {
  id: string;
  name: string;
  drug_class: string | null;
  dose: string | null;
  status: string;
  started: string | null;
  stopped: string | null;
  source: string;
  forgotten: boolean;
  danger: boolean;
};

export type SourceDoc = { name: string; text: string };
export type Patient = { name: string; age: number; sex: string; mrn: string; note: string };

export type ReconcileAction = {
  entity: string;
  kept_status: string;
  kept_source: string;
  forgotten: { status: string; source: string }[];
  reason: string;
};

export type Alert = {
  severity: string;
  effect: string;
  proposed_drug: string;
  conflicting_drug: string;
  mechanism: string;
  management: string;
  patient_source: string;
  evidence_source: string;
};

export type SafetyResult = {
  proposed: { name: string; drug_class: string };
  verdict: "block" | "ok";
  alerts: Alert[];
  alternatives: string[];
};

export type Candidate = { name: string; drug_class: string; indication: string };

export type Handoff = {
  conditions: string[];
  medications: { name: string; dose: string | null; drug_class: string | null }[];
  allergies: { substance: string; reaction: string | null }[];
  discontinued: { name: string; stopped: string | null }[];
  text: string;
};

export type RecallResult = {
  answer: string;
  evidence: { text: string; source: string }[];
  engine: string;
};

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}
async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

export type FactSummary = { kind: string; label: string; status: string; source: string };

export const api = {
  patient: () => get<{ patient: Patient; documents: SourceDoc[] }>("/api/patient"),
  records: () => get<{ facts: FactSummary[]; count: number }>("/api/records"),
  addText: (text: string, source?: string) =>
    post<{ ok: boolean; extracted?: FactSummary[]; count?: number; error?: string }>(
      "/api/records/text", { text, source }),
  addManual: (kind: string, data: Record<string, unknown>) =>
    post<{ ok: boolean; added?: FactSummary; error?: string }>(
      "/api/records/manual", { kind, data }),
  resetRecords: () => post<{ ok: boolean; count: number }>("/api/records/reset", {}),
  clearRecords: () => post<{ ok: boolean; count: number }>("/api/records/clear", {}),
  timeline: () => get<{ medications: Med[] }>("/api/timeline"),
  reconcile: () =>
    get<{ actions: ReconcileAction[]; current_medications: any[] }>("/api/reconcile"),
  handoff: () => get<Handoff>("/api/handoff"),
  candidates: () =>
    get<{ candidates: Candidate[]; default: Candidate }>("/api/candidates"),
  safetyCheck: (name: string, drug_class: string, indication?: string) =>
    post<SafetyResult>("/api/safety-check", { name, drug_class, indication }),
  recall: (query: string) => post<RecallResult>("/api/recall", { query }),
  erase: () => post<{ status: string }>("/api/erase", {}),
};
