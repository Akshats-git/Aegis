"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { ChevronDown, LogOut, Pencil } from "lucide-react";

function initials(name?: string | null, email?: string | null) {
  const base = name || email || "U";
  return base
    .split(/[\s@]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

export function ProfileMenu() {
  const { data: session } = useSession();
  const user = session?.user;
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const avatar = user?.image ? (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={user.image} alt="" className="h-8 w-8 rounded-full" />
  ) : (
    <span className="grid h-8 w-8 place-items-center rounded-full bg-rose/15 text-xs font-semibold text-rose">
      {initials(user?.name, user?.email)}
    </span>
  );

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full border border-line py-1 pl-1 pr-2 text-sm transition-colors hover:bg-field"
      >
        {avatar}
        <ChevronDown
          className={`h-4 w-4 text-muted transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-60 overflow-hidden rounded-xl border border-line bg-bg/95 p-1 shadow-2xl backdrop-blur-xl"
        >
          <div className="border-b border-line px-3 py-2.5">
            <div className="truncate text-sm font-medium">{user?.name || "Your account"}</div>
            <div className="truncate text-xs text-muted">{user?.email}</div>
          </div>
          <Link
            href="/profile"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="mt-1 flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted transition-colors hover:bg-field hover:text-ink"
          >
            <Pencil className="h-4 w-4" /> Edit profile
          </Link>
          <button
            role="menuitem"
            onClick={() => signOut()}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted transition-colors hover:bg-field hover:text-danger"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}
