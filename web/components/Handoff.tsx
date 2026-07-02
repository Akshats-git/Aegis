"use client";

import { HeartPulse, Pill, ShieldAlert, Clock } from "lucide-react";
import type { Handoff as HandoffData } from "@/lib/api";
import { Card, Reveal, SectionTitle, Badge } from "./ui";

function Row({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2">
        {icon}
        <span className="label">{title}</span>
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

export function Handoff({ data }: { data: HandoffData }) {
  return (
    <section className="mx-auto mt-24 max-w-6xl px-6">
      <Reveal>
        <SectionTitle
          eyebrow="Share in seconds"
          title="Your health summary for any doctor"
          desc="Everything a new doctor needs to know about you — accurate and up to date — ready the moment you walk in."
        />
      </Reveal>
      <Reveal>
        <Card className="grid gap-6 sm:grid-cols-2">
          <Row icon={<HeartPulse className="h-4 w-4 text-teal" />} title="Active conditions">
            {data.conditions.map((c) => (
              <Badge key={c}>{c}</Badge>
            ))}
          </Row>
          <Row icon={<Pill className="h-4 w-4 text-teal" />} title="Current medications">
            {data.medications.map((m) => (
              <Badge key={m.name} tone={m.drug_class === "MAOI" ? "danger" : "teal"}>
                {m.name} {m.dose ? `· ${m.dose}` : ""}
              </Badge>
            ))}
          </Row>
          <Row icon={<ShieldAlert className="h-4 w-4 text-warn" />} title="Allergies">
            {data.allergies.map((a) => (
              <Badge key={a.substance} tone="warn">
                {a.substance} ({a.reaction})
              </Badge>
            ))}
          </Row>
          <Row icon={<Clock className="h-4 w-4 text-muted" />} title="Recently discontinued">
            {data.discontinued.map((d) => (
              <Badge key={d.name} tone="muted">
                {d.name} · stopped {d.stopped}
              </Badge>
            ))}
          </Row>
        </Card>
      </Reveal>
    </section>
  );
}
