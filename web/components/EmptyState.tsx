"use client";

import Link from "next/link";
import { FilePlus2 } from "lucide-react";

export function EmptyState({
  title = "Nothing here yet",
  desc,
}: {
  title?: string;
  desc?: string;
}) {
  return (
    <div className="card flex flex-col items-center gap-4 p-12 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-2xl bg-rose/10">
        <FilePlus2 className="h-6 w-6 text-rose" />
      </div>
      <div>
        <h3 className="text-xl font-semibold">{title}</h3>
        {desc && <p className="mx-auto mt-1 max-w-md text-sm text-muted">{desc}</p>}
      </div>
      <Link
        href="/records"
        className="inline-flex items-center gap-2 rounded-xl bg-rose px-4 py-2.5 text-sm font-semibold text-black transition-transform hover:scale-[1.02]"
      >
        Add your records
      </Link>
    </div>
  );
}

export function PageLoader() {
  return (
    <div className="grid place-items-center py-24">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-rose border-t-transparent" />
    </div>
  );
}
