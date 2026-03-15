"use client";

import { useState } from "react";
import {
  Play,
  Pause,
  CheckCircle,
  Clock,
  XCircle,
  BarChart3,
} from "lucide-react";

/* ── Types ── */

interface SchedulerStatus {
  running: boolean;
  cycleCount: number;
  modeDistribution: { mode: string; count: number }[];
}

interface FinetuneRun {
  id: string;
  date: string;
  type: "micro" | "full";
  archetype: string;
  loss: number;
  deployed: boolean;
}

interface Proposal {
  id: string;
  title: string;
  description: string;
  status: "pending" | "approved" | "rejected";
  safetyScore: number;
  improvementScore: number;
}

interface EvolutionMetrics {
  placeholder?: boolean;
}

interface EvolutionDashboardProps {
  schedulerStatus: SchedulerStatus;
  finetuneHistory: FinetuneRun[];
  proposals: Proposal[];
  metrics: EvolutionMetrics;
}

type Tab = "scheduler" | "finetune" | "proposals" | "metrics";

const TABS: { key: Tab; label: string }[] = [
  { key: "scheduler", label: "Scheduler" },
  { key: "finetune", label: "Fine-tune" },
  { key: "proposals", label: "Proposals" },
  { key: "metrics", label: "Metrics" },
];

const PROPOSAL_STATUS_CONFIG: Record<
  Proposal["status"],
  { icon: typeof CheckCircle; className: string }
> = {
  pending: {
    icon: Clock,
    className: "text-yellow-400 bg-yellow-500/15 border-yellow-500/30",
  },
  approved: {
    icon: CheckCircle,
    className: "text-green-400 bg-green-500/15 border-green-500/30",
  },
  rejected: {
    icon: XCircle,
    className: "text-red-400 bg-red-500/15 border-red-500/30",
  },
};

/* ── Sub-panels ── */

function SchedulerTab({ status }: { status: SchedulerStatus }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-slate-300">Status</span>
        {status.running ? (
          <span className="inline-flex items-center gap-1 rounded-full border border-green-500/30 bg-green-500/15 px-2.5 py-0.5 text-xs font-medium text-green-400">
            <Play className="h-3 w-3" />
            Running
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full border border-slate-600 bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-400">
            <Pause className="h-3 w-3" />
            Stopped
          </span>
        )}
      </div>

      <div>
        <span className="text-sm font-medium text-slate-300">Cycles completed: </span>
        <span className="text-sm text-slate-100">{status.cycleCount}</span>
      </div>

      <div>
        <p className="mb-2 text-sm font-medium text-slate-300">Mode Distribution</p>
        <div className="flex flex-col gap-1.5">
          {(status.modeDistribution ?? []).map((m) => (
            <div key={m.mode} className="flex items-center gap-2">
              <span className="w-24 text-xs text-slate-400">{m.mode}</span>
              <div className="flex-1 h-2 rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-indigo-500"
                  style={{
                    width: `${
                      status.cycleCount > 0
                        ? (m.count / status.cycleCount) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
              <span className="w-8 text-right text-xs text-slate-500">{m.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FinetuneTab({ history }: { history: FinetuneRun[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-slate-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-900">
            <th className="px-3 py-2 text-left font-medium text-slate-400">Date</th>
            <th className="px-3 py-2 text-left font-medium text-slate-400">Type</th>
            <th className="px-3 py-2 text-left font-medium text-slate-400">Archetype</th>
            <th className="px-3 py-2 text-left font-medium text-slate-400">Loss</th>
            <th className="px-3 py-2 text-left font-medium text-slate-400">Deployed</th>
          </tr>
        </thead>
        <tbody>
          {history.length === 0 && (
            <tr>
              <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                No fine-tune runs
              </td>
            </tr>
          )}
          {history.map((run) => (
            <tr
              key={run.id}
              className="border-b border-slate-800/50 last:border-0"
            >
              <td className="px-3 py-2 font-mono text-xs text-slate-400">
                {run.date}
              </td>
              <td className="px-3 py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    run.type === "micro"
                      ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                      : "bg-purple-500/15 text-purple-400 border border-purple-500/30"
                  }`}
                >
                  {run.type}
                </span>
              </td>
              <td className="px-3 py-2 text-slate-300">{run.archetype}</td>
              <td className="px-3 py-2 font-mono text-xs text-slate-300">
                {run.loss.toFixed(4)}
              </td>
              <td className="px-3 py-2">
                {run.deployed ? (
                  <CheckCircle className="h-4 w-4 text-green-400" />
                ) : (
                  <span className="text-xs text-slate-500">--</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProposalsTab({ proposals }: { proposals: Proposal[] }) {
  return (
    <div className="flex flex-col gap-3">
      {proposals.length === 0 && (
        <p className="py-8 text-center text-sm text-slate-500">No proposals</p>
      )}
      {proposals.map((p) => {
        const config = PROPOSAL_STATUS_CONFIG[p.status];
        const Icon = config.icon;
        return (
          <div
            key={p.id}
            className="flex flex-col gap-2 rounded-lg border border-slate-800 bg-slate-900 p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <h4 className="text-sm font-medium text-slate-200">{p.title}</h4>
              <span
                className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${config.className}`}
              >
                <Icon className="h-3 w-3" />
                {p.status}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-slate-400">{p.description}</p>
            <div className="flex gap-4">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] uppercase tracking-wider text-slate-500">
                  Safety
                </span>
                <div className="h-1.5 w-16 rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-green-500"
                    style={{ width: `${p.safetyScore * 100}%` }}
                  />
                </div>
                <span className="text-[10px] text-slate-500">
                  {(p.safetyScore * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] uppercase tracking-wider text-slate-500">
                  Impact
                </span>
                <div className="h-1.5 w-16 rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-indigo-500"
                    style={{ width: `${p.improvementScore * 100}%` }}
                  />
                </div>
                <span className="text-[10px] text-slate-500">
                  {(p.improvementScore * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function MetricsTab() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-slate-500">
      <BarChart3 className="h-10 w-10" />
      <p className="text-sm">Metrics charts coming soon</p>
    </div>
  );
}

/* ── Main component ── */

export default function EvolutionDashboard({
  schedulerStatus,
  finetuneHistory,
  proposals,
}: EvolutionDashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>("scheduler");

  return (
    <div className="flex flex-col gap-4 rounded-lg border border-slate-800 bg-slate-950 p-5">
      <h2 className="text-lg font-semibold text-slate-100">Evolution Dashboard</h2>

      {/* Tabs */}
      <div className="flex gap-1 rounded-md bg-slate-900 p-1">
        {TABS.map((tab) => (
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

      {/* Content */}
      <div>
        {activeTab === "scheduler" && <SchedulerTab status={schedulerStatus} />}
        {activeTab === "finetune" && <FinetuneTab history={finetuneHistory} />}
        {activeTab === "proposals" && <ProposalsTab proposals={proposals} />}
        {activeTab === "metrics" && <MetricsTab />}
      </div>
    </div>
  );
}
