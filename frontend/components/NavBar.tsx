"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useStore } from "@/lib/store";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Home" },
  { href: "/network", label: "Network" },
  { href: "/groups", label: "Groups" },
  { href: "/events", label: "Events" },
  { href: "/learn", label: "Learn" },
];

export default function NavBar() {
  const pathname = usePathname();
  const token = useStore((s) => s.token);

  // Don't show on auth/onboarding pages
  if (!token || ["/login", "/onboarding"].includes(pathname)) return null;

  return (
    <nav className="sticky top-0 z-40 border-b border-gray-800 bg-gray-950/95 backdrop-blur">
      <div className="mx-auto flex h-12 max-w-7xl items-center px-4">
        <Link href="/dashboard" className="mr-8 text-sm font-bold text-purple-400">
          NexusMind
        </Link>
        <div className="flex gap-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
                pathname === item.href
                  ? "bg-gray-800 text-white font-medium"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Link
            href="/profile"
            className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-600 text-xs font-bold text-white hover:bg-purple-500"
          >
            P
          </Link>
        </div>
      </div>
    </nav>
  );
}
