"use client";

import { useRouter } from "next/navigation";
import { Erase } from "@/components/Erase";

export default function PrivacyPage() {
  const router = useRouter();
  return <Erase onErased={() => router.push("/")} />;
}
