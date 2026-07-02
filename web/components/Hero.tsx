"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldPlus, LogOut, ChevronDown } from "lucide-react";
import { Badge } from "./ui";

type SessionUser = { name?: string | null; email?: string | null; image?: string | null };

function initials(name?: string | null, email?: string | null) {
  const base = name || email || "U";
  return base.split(/[\s@]/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("");
}

function ProfileMenu({ user, onSignOut }: { user: SessionUser; onSignOut: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-full border border-line bg-white/5 py-1 pl-1 pr-2.5 transition-colors hover:bg-white/10"
      >
        {user.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.image} alt="" className="h-7 w-7 rounded-full" />
        ) : (
          <span className="grid h-7 w-7 place-items-center rounded-full bg-teal/15 text-xs font-semibold text-teal">
            {initials(user.name, user.email)}
          </span>
        )}
        <span className="hidden text-sm sm:inline">{user.name || "Account"}</span>
        <ChevronDown className="h-3.5 w-3.5 text-muted" />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="absolute right-0 z-20 mt-2 w-52 overflow-hidden rounded-xl border border-line bg-bg/95 backdrop-blur-xl"
          >
            <div className="border-b border-line px-4 py-3">
              <div className="truncate text-sm font-medium">{user.name || "Guest"}</div>
              <div className="truncate text-xs text-muted">{user.email}</div>
            </div>
            <button
              onClick={onSignOut}
              className="flex w-full items-center gap-2 px-4 py-3 text-sm text-danger hover:bg-white/5"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Hero({ user, onSignOut }: { user: SessionUser; onSignOut: () => void }) {
  const firstName = (user.name || "there").split(" ")[0];
  return (
    <header className="relative mx-auto max-w-6xl px-6 pt-8">
      <nav className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-xl border border-teal/30 bg-teal/10">
            <ShieldPlus className="h-5 w-5 text-teal" />
          </div>
          <span className="text-lg font-semibold tracking-tight">Aegis</span>
        </div>
        <ProfileMenu user={user} onSignOut={onSignOut} />
      </nav>

      <div className="relative mt-14 overflow-hidden rounded-3xl border border-line bg-panel p-8 backdrop-blur-xl sm:p-12">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-teal/10 blur-3xl" />
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        >
          <Badge tone="teal">Your personal health record</Badge>
          <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
            Welcome back, <span className="gradient-text">{firstName}</span>.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted">
            Keep all your health records in one place and always up to date. Any new doctor
            instantly knows what matters, and{" "}
            <span className="text-ink">you&apos;re warned before a medicine could harm you.</span>
          </p>
        </motion.div>
      </div>
    </header>
  );
}
