"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  ShieldPlus, LayoutDashboard, FolderHeart, Pill, ShieldCheck,
  ClipboardList, MessageCircle, Lock, Menu, X,
} from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ProfileMenu } from "@/components/ProfileMenu";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/records", label: "My records", icon: FolderHeart },
  { href: "/medications", label: "Medications", icon: Pill },
  { href: "/safety", label: "Safety check", icon: ShieldCheck },
  { href: "/summary", label: "Doctor summary", icon: ClipboardList },
  { href: "/ask", label: "Ask Aegis", icon: MessageCircle },
  { href: "/privacy", label: "Privacy", icon: Lock },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
              active ? "bg-rose/10 text-rose" : "text-muted hover:bg-field hover:text-ink"
            }`}
          >
            <Icon className="h-[18px] w-[18px]" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2.5">
      <div className="grid h-9 w-9 place-items-center rounded-xl border border-rose/30 bg-rose/10">
        <ShieldPlus className="h-5 w-5 text-rose" />
      </div>
      <span className="text-lg font-semibold tracking-tight">Aegis</span>
    </Link>
  );
}

export function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-line bg-panel p-4 backdrop-blur-xl md:flex">
        <div className="px-1 pb-6 pt-2">
          <Logo />
        </div>
        <NavLinks />
      </aside>

      {/* Mobile top bar */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-bg/80 px-4 py-3 backdrop-blur-xl md:hidden">
        <Logo />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <ProfileMenu />
          <button
            onClick={() => setOpen(true)}
            className="grid h-9 w-9 place-items-center rounded-lg border border-line"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
              className="fixed inset-0 z-40 bg-black/60 md:hidden"
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "tween", duration: 0.25 }}
              className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-line bg-bg p-4 md:hidden"
            >
              <div className="flex items-center justify-between px-1 pb-6 pt-2">
                <Logo />
                <button onClick={() => setOpen(false)} className="grid h-9 w-9 place-items-center rounded-lg border border-line">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <NavLinks onNavigate={() => setOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
