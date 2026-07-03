"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Loader2, Check } from "lucide-react";
import { Card, SectionTitle, Button } from "@/components/ui";

export default function ProfilePage() {
  const { data: session, update } = useSession();
  const user = session?.user as { id?: string; name?: string; email?: string } | undefined;

  const [name, setName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  // Prefill the name once the session is available.
  useEffect(() => {
    if (user?.name) setName(user.name);
  }, [user?.name]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    setLoading(true);
    try {
      const body: Record<string, string> = {};
      if (name.trim() && name.trim() !== user?.name) body.name = name.trim();
      if (newPassword) {
        body.new_password = newPassword;
        body.current_password = currentPassword;
      }
      if (Object.keys(body).length === 0) {
        setError("Nothing to update.");
        setLoading(false);
        return;
      }
      const r = await fetch("/backend/auth/update", {
        method: "POST",
        headers: { "content-type": "application/json", "X-User-Id": user?.id ?? "" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || "Could not save your changes.");
      }
      const updated = (await r.json()) as { name: string };
      // Reflect the new name in the session (triggers the jwt "update" callback).
      if (body.name) await update({ name: updated.name });
      setCurrentPassword("");
      setNewPassword("");
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <SectionTitle
        eyebrow="Account"
        title="Edit profile"
        desc="Update your display name or change your password."
      />

      <Card>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Name" value={name} onChange={setName} placeholder="Your name" autoComplete="name" />

          <div>
            <span className="mb-1.5 block text-xs font-medium text-muted">Email</span>
            <div className="w-full cursor-not-allowed rounded-xl border border-line bg-field px-3.5 py-3 text-sm text-muted">
              {user?.email || "—"}
            </div>
          </div>

          <div className="border-t border-line pt-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
              Change password
            </p>
            <div className="space-y-3">
              <Field
                label="Current password"
                type="password"
                value={currentPassword}
                onChange={setCurrentPassword}
                placeholder="Required to set a new password"
                autoComplete="current-password"
              />
              <Field
                label="New password"
                type="password"
                value={newPassword}
                onChange={setNewPassword}
                placeholder="At least 8 characters"
                autoComplete="new-password"
              />
            </div>
          </div>

          {error && (
            <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
          )}
          {saved && (
            <p className="flex items-center gap-2 rounded-lg bg-rose/10 px-3 py-2 text-sm text-rose">
              <Check className="h-4 w-4" /> Profile updated.
            </p>
          )}

          <Button disabled={loading} className="w-full">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Save changes
          </Button>
        </form>
      </Card>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  ...props
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange">) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-muted">{label}</span>
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-line bg-field px-3.5 py-3 text-sm text-ink outline-none transition-colors placeholder:text-muted/60 focus:border-rose/50"
      />
    </label>
  );
}
