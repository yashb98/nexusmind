"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useStore } from "@/lib/store";
import { motion } from "framer-motion";

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

  if (!token || ["/login", "/onboarding"].includes(pathname)) return null;

  return (
    <motion.nav
      initial={{ y: -48, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="sticky top-0 z-40 border-b border-gray-800 bg-gray-950/95 backdrop-blur"
    >
      <div className="mx-auto flex h-12 max-w-7xl items-center px-4">
        <Link href="/dashboard" className="mr-8 text-sm font-bold text-purple-400">
          NexusMind
        </Link>
        <div className="flex gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <motion.div key={item.href} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.97 }} className="relative">
                <Link
                  href={item.href}
                  aria-current={isActive ? "page" : undefined}
                  className={`relative block rounded-lg px-3 py-1.5 text-sm transition-colors ${
                    isActive ? "bg-gray-800 text-white font-medium" : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-underline"
                      className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-purple-500"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              </motion.div>
            );
          })}
        </div>
        <div className="ml-auto">
          <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="/profile"
              aria-label="Profile"
              className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-600 text-xs font-bold text-white hover:bg-purple-500"
            >
              P
            </Link>
          </motion.div>
        </div>
      </div>
    </motion.nav>
  );
}
