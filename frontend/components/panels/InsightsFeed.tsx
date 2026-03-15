"use client";

import { useState } from "react";
import { CheckCircle, AlertTriangle, XCircle, BookOpen } from "lucide-react";

type VerificationStatus = "accepted" | "provisional" | "rejected";
type FilterTab = "all" | "verified" | "unverified";

interface Insight {
  id: string;
  text: string;
  topic: string;
  importance: number; // 0-1
  status: VerificationStatus;
}

interface InsightsFeedProps {
  insights: Insight[];
  onTeachMe: (insightId: string) => void;
}

const STATUS_CONFIG: Record<
  VerificationStatus,
  { icon: typeof CheckCircle; label: string; className: string }
> = {
  accepted: {
    icon: CheckCircle,
    label: "Accepted",
    className: "text-green-400 bg-green-500/15 border-green-500/30",
  },
  provisional: {
    icon: AlertTriangle,
    label: "Provisional",
    className: "text-yellow-400 bg-yellow-500/15 border-yellow-500/30",
  },
  rejected: {
    icon: XCircle,
    label: "Rejected",
    className: "text-red-400 bg-red-500/15 border-red-500/30",
  },
};

function StatusBadge({ status }: { status: VerificationStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${config.className}`}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
}

const TAB_OPTIONS: { key: FilterTab; label: string }[] = [
  { key: "all", label: "All" },
  { key: "verified", label: "Verified" },
  { key: "unverified", label: "Unverified" },
];

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

      {/* Filter tabs */}
      <div className="flex gap-1 rounded-md bg-slate-900 p-1">
        {TAB_OPTIONS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 rounded px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-slate-700 text-slate-100"
                : "text-slate-400 hover:text-slate-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Cards */}
      <div className="flex flex-col gap-3 max-h-[600px] overflow-y-auto pr-1">
        {filtered.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">No insights found</p>
        )}
        {filtered.map((insight) => (
          <div
            key={insight.id}
            className="flex flex-col gap-2.5 rounded-lg border border-slate-800 bg-slate-900 p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm leading-relaxed text-slate-300">{insight.text}</p>
              <StatusBadge status={insight.status} />
            </div>

            {/* Topic tag */}
            <span className="self-start rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-400 border border-slate-700">
              {insight.topic}
            </span>

            {/* Importance bar */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wider text-slate-500">
                Importance
              </span>
              <div className="flex-1 h-1.5 rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-indigo-500"
                  style={{ width: `${insight.importance * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-500">
                {(insight.importance * 100).toFixed(0)}%
              </span>
            </div>

            {/* Teach me button */}
            <button
              onClick={() => onTeachMe(insight.id)}
              className="mt-1 flex items-center justify-center gap-1.5 self-start rounded-md border border-indigo-500/30 bg-indigo-600/10 px-3 py-1.5 text-xs font-medium text-indigo-400 transition-colors hover:bg-indigo-600/20"
            >
              <BookOpen className="h-3.5 w-3.5" />
              Teach me
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
