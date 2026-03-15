"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const token = useStore((s) => s.token);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    } else {
      setChecked(true);
    }
  }, [token, router]);

  if (!checked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  return <>{children}</>;
}
