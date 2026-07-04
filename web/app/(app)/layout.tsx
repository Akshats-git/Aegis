"use client";

import { useSession } from "next-auth/react";
import { Loader2 } from "lucide-react";
import { setUserId } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import { Sidebar } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ProfileMenu } from "@/components/ProfileMenu";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="grid min-h-screen place-items-center">
        <Loader2 className="h-6 w-6 animate-spin text-rose" />
      </div>
    );
  }

  if (status === "unauthenticated" || !session) {
    return <SignIn />;
  }

  // Make the signed-in user's id available to every API call before pages fetch.
  const uid = (session.user as { id?: string } | undefined)?.id;
  if (uid) setUserId(uid);

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="md:pl-64">
        {/* Desktop top bar (mobile shows these controls in the Sidebar top bar). */}
        <header className="sticky top-0 z-20 hidden items-center justify-end gap-2 border-b border-line bg-bg/70 px-8 py-3 backdrop-blur-xl md:flex">
          <ThemeToggle />
          <ProfileMenu />
        </header>
        <main className="mx-auto max-w-6xl px-5 py-8 sm:px-10 sm:py-12">{children}</main>
      </div>
    </div>
  );
}
