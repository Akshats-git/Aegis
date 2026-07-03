"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { motion } from "framer-motion";
import { ShieldPlus, FolderHeart, ShieldCheck, Lock, Loader2 } from "lucide-react";

const FEATURES = [
  { icon: FolderHeart, text: "Every record kept in one place." },
  { icon: ShieldCheck, text: "Get warned about unsafe medicines." },
  { icon: Lock, text: "Delete your data whenever you want." },
];

type Mode = "signin" | "signup";

export function SignIn() {
  const [mode, setMode] = useState<Mode>("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "signup") {
        const r = await fetch("/backend/auth/register", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ email, password, name }),
        });
        if (!r.ok) {
          const d = await r.json().catch(() => ({}));
          throw new Error(d.detail || "Could not create your account.");
        }
      }
      const res = await signIn("credentials", { email, password, redirect: false });
      if (!res?.ok) {
        throw new Error(
          mode === "signup"
            ? "Account created, but sign in failed. Try signing in."
            : "Incorrect email or password.",
        );
      }
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  const isSignup = mode === "signup";

  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        className="relative w-full max-w-[420px]"
      >
        {/* soft glow behind the card */}
        <div className="pointer-events-none absolute -inset-6 -z-10 rounded-[2rem] bg-rose/10 blur-3xl" />

        <div className="card overflow-hidden p-8 sm:p-10">
          <div className="flex flex-col items-center text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl border border-rose/30 bg-rose/10">
              <ShieldPlus className="h-7 w-7 text-rose" />
            </div>
            <h1 className="mt-5 text-2xl font-semibold tracking-tight">
              {isSignup ? "Create your account" : "Welcome back"}
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Aegis keeps your medicines up to date. It warns you before a new one could
              harm you.
            </p>
          </div>

          <form onSubmit={onSubmit} className="mt-8 space-y-3">
            {isSignup && (
              <Field
                label="Name"
                type="text"
                value={name}
                onChange={setName}
                placeholder="Your name"
                autoComplete="name"
              />
            )}
            <Field
              label="Email"
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
            <Field
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
              placeholder={isSignup ? "At least 8 characters" : "Your password"}
              autoComplete={isSignup ? "new-password" : "current-password"}
              required
            />

            {error && (
              <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-rose px-4 py-3 text-sm font-semibold text-black transition-transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-60"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSignup ? "Create account" : "Sign in"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-muted">
            {isSignup ? "Already have an account?" : "New to Aegis?"}{" "}
            <button
              type="button"
              onClick={() => {
                setMode(isSignup ? "signin" : "signup");
                setError("");
              }}
              className="font-semibold text-rose hover:underline"
            >
              {isSignup ? "Sign in" : "Create one"}
            </button>
          </p>

          <div className="mt-8 space-y-3 border-t border-line pt-6">
            {FEATURES.map((f) => (
              <div key={f.text} className="flex items-center gap-3 text-sm text-muted">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/5">
                  <f.icon className="h-4 w-4 text-rose" />
                </div>
                <span>{f.text}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="mt-5 text-center text-xs text-muted">
          Your data is private. You can delete it anytime.
        </p>
      </motion.div>
    </main>
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
    <label className="block text-left">
      <span className="mb-1.5 block text-xs font-medium text-muted">{label}</span>
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-line bg-white/5 px-3.5 py-3 text-sm text-ink outline-none transition-colors placeholder:text-muted/60 focus:border-rose/50"
      />
    </label>
  );
}
