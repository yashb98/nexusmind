"use client";

import { useHydrateStore } from "@/lib/store";

export default function StoreProvider({ children }: { children: React.ReactNode }) {
  useHydrateStore();
  return <>{children}</>;
}
