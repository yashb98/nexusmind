"use client";

import { useState } from "react";
import { CheckCircle, AlertTriangle, XCircle, BookOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type VerificationStatus = "accepted" | "provisional" | "rejected";
type FilterTab = "all" | "verified" | "unverified";

interface Insight {
  id: string;
  text: string;
  topic: string;
  importance: number;
  status: VerificationStatus;
}

interface InsightsFeedProps {
  insights: Insight[];
  onTeachMe: (insightId: string) => void;
}

const STATUS_CONFIG: Record<VerificationStatus, { icon: typeof CheckCircle; label: string; className: string }> = {
  accepted: { icon: CheckCircle, label: "Accepted", className: "text-green-400 bg-green-500/15 border-green-500/30" },
  provisional: { icon: AlertTriangle, label: "Provisional", className: "text-yellow-400 bg-yellow-500/15 border-yellow-500/30" },
  rejected: { icon: XCircle, label: "Rejected", className: "text-red-400 bg-red-500/15 border-red-500/30" },
};

const TAB_OPTIONS: { key: FilterTab; label: string }[] = [
  { key: "all", label: "All" },
  { key: "verified", label: "Verified" },
  { key: "unverified", label: "Unverified" },
];

const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.06, duration: 0.3, ease: "easeOut" } }),
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
};

function StatusBadge({ status }: { status: VerificationStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${config.className}`}>
      <Icon className="h-3 w-3" aria-hidden="true" />
      {config.label}
    </span>
  );
}

export default function InsightsFeed({ insights, onTeachMe }: InsightsFeedProps) {
  const [activeTab, setActiveTab] = useState<FilterTab>("all");

  const filtered = insights.filter((insight) => {
    if (activeTab === "verified") return insight.status === "accepted";
    if (activeTab === "unverified") return insight.status !== "accepted";
    return true;
  });

  return (
    <div className="flex flex-col gap-4 rounded-lg border border-slate-800 bg-slate-950 p-5">
      <h2 className="text-lg font-semibold text-slate-100">Insights</h2>

      <div role="tablist" aria-label="Filter insights" className="relative flex gap-1 rounded-md bg-slate-900 p-1">
        {TAB_OPTIONS.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveTab(tab.key)}
              className={`relative flex-1 rounded px-3 py-1.5 text-xs font-medium transition-colors z-10 ${isActive ? "text-slate-100" : "text-slate-400 hover:text-slate-300"}`}
            >
              {isActive && (
                <motion.span layoutId="insight-tab-indicator" className="absolute inset-0 rounded bg-slate-700" style={{ zIndex: -1 }} transition={{ type: "spring", stiffness: 380, damping: 30 }} />
              )}
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-3 max-h-[600px] overflow-y-auto pr-1">
        {filtered.length === 0 && <p className="py-8 text-center text-sm text-slate-500">No insights found</p>}
        <AnimatePresence mode="popLayout">
          {filtered.map((insight, i) => (
            <motion.div key={insight.id} custom={i} variants={cardVariants} initial="hidden" animate="visible" exit="exit" layout className="flex flex-col gap-2.5 rounded-lg border border-slate-800 bg-slate-900 p-4">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm leading-relaxed text-slate-300">{insight.text}</p>
                <StatusBadge status={insight.status} />
              </div>
              <span className="self-start rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-400 border border-slate-700">{insight.topic}</span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wider text-slate-500">Importance</span>
                <div role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(insight.importance * 100)} aria-label={`Importance: ${Math.round(insight.importance * 100)}%`} className="flex-1 h-1.5 rounded-full bg-slate-800">
                  <motion.div className="h-full rounded-full bg-indigo-500" initial={{ width: 0 }} animate={{ width: `${insight.importance * 100}%` }} transition={{ duration: 0.7, ease: "easeOut", delay: i * 0.06 }} />
                </div>
                <span className="text-[10px] text-slate-500">{(insight.importance * 100).toFixed(0)}%</span>
              </div>
              <button onClick={() => onTeachMe(insight.id)} className="mt-1 flex items-center justify-center gap-1.5 self-start rounded-md border border-indigo-500/30 bg-indigo-600/10 px-3 py-1.5 text-xs font-medium text-indigo-400 transition-colors hover:bg-indigo-600/20">
                <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
                Teach me
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
