"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("card p-5", className)}>{children}</div>;
}

export function SectionTitle({
  eyebrow,
  title,
  desc,
}: {
  eyebrow: string;
  title: string;
  desc?: string;
}) {
  return (
    <div className="mb-5">
      <div className="label text-rose">{eyebrow}</div>
      <h2 className="mt-1 text-2xl font-semibold tracking-tight">{title}</h2>
      {desc && <p className="mt-1 max-w-2xl text-sm text-muted">{desc}</p>}
    </div>
  );
}

export function Badge({
  children,
  tone = "default",
  className,
}: {
  children: React.ReactNode;
  tone?: "default" | "rose" | "danger" | "warn" | "muted";
  className?: string;
}) {
  const tones: Record<string, string> = {
    default: "text-ink",
    rose: "border-rose/30 bg-rose/10 text-rose",
    danger: "border-danger/40 bg-danger/10 text-danger",
    warn: "border-warn/30 bg-warn/10 text-warn",
    muted: "text-muted",
  };
  return <span className={cn("chip", tones[tone], className)}>{children}</span>;
}

export function Button({
  children,
  onClick,
  disabled,
  tone = "primary",
  className,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  tone?: "primary" | "ghost" | "danger";
  className?: string;
}) {
  const tones: Record<string, string> = {
    primary: "bg-rose text-black hover:bg-rose/90",
    ghost: "border border-line bg-field text-ink hover:bg-line",
    danger: "border border-danger/40 bg-danger/10 text-danger hover:bg-danger/20",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all disabled:cursor-not-allowed disabled:opacity-50",
        tones[tone],
        className,
      )}
    >
      {children}
    </button>
  );
}
