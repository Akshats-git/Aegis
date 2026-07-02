"use client";

import { signIn } from "next-auth/react";
import { motion } from "framer-motion";
import { ShieldPlus, FolderHeart, ShieldCheck, Lock } from "lucide-react";

const googleEnabled = process.env.NEXT_PUBLIC_GOOGLE_ENABLED === "true";

const FEATURES = [
  { icon: FolderHeart, text: "Every record kept in one place." },
  { icon: ShieldCheck, text: "Get warned about unsafe medicines." },
  { icon: Lock, text: "Delete your data whenever you want." },
];

export function SignIn() {
  return (
    <main className="grid min-h-screen place-items-center px-5 py-10">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        className="relative w-full max-w-[420px]"
      >
        {/* soft glow behind the card */}
        <div className="pointer-events-none absolute -inset-6 -z-10 rounded-[2rem] bg-teal/10 blur-3xl" />

        <div className="card overflow-hidden p-8 sm:p-10">
          <div className="flex flex-col items-center text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl border border-teal/30 bg-teal/10">
              <ShieldPlus className="h-7 w-7 text-teal" />
            </div>
            <h1 className="mt-5 text-2xl font-semibold tracking-tight">
              All your health records, in one place
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Aegis keeps your medicines up to date. It warns you before a new one could
              harm you.
            </p>
          </div>

          <div className="mt-8 space-y-3">
            {googleEnabled && (
              <button
                onClick={() => signIn("google", { callbackUrl: "/" })}
                className="flex w-full items-center justify-center gap-3 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-black transition-transform hover:scale-[1.01] active:scale-[0.99]"
              >
                <GoogleIcon /> Continue with Google
              </button>
            )}
            <button
              onClick={() => signIn("guest", { callbackUrl: "/" })}
              className={`flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition-transform hover:scale-[1.01] active:scale-[0.99] ${
                googleEnabled ? "border border-line bg-white/5 text-ink" : "bg-teal text-black"
              }`}
            >
              Continue as guest
            </button>
          </div>

          {!googleEnabled && (
            <p className="mt-3 text-center text-xs text-muted">
              Google sign in is not set up yet. Use guest to try it out.
            </p>
          )}

          <div className="mt-8 space-y-3 border-t border-line pt-6">
            {FEATURES.map((f) => (
              <div key={f.text} className="flex items-center gap-3 text-sm text-muted">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/5">
                  <f.icon className="h-4 w-4 text-teal" />
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

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1Z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84Z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84C6.71 7.3 9.14 5.38 12 5.38Z" />
    </svg>
  );
}
