"use client";

import { Shield } from "lucide-react";

interface Permission {
  agentName: string;
  level: number;
  levelDescription: string;
}

interface AuditEntry {
  timestamp: string;
  action: string;
  category: string;
}

interface PrivacyDashboardProps {
  permissions: Permission[];
  auditLog: AuditEntry[];
}

const LEVEL_COLORS: Record<number, string> = {
  0: "bg-slate-500/20 text-slate-400",
  1: "bg-green-500/20 text-green-400",
  2: "bg-blue-500/20 text-blue-400",
  3: "bg-yellow-500/20 text-yellow-400",
  4: "bg-orange-500/20 text-orange-400",
  5: "bg-red-500/20 text-red-400",
};

export default function PrivacyDashboard({
  permissions,
  auditLog,
}: PrivacyDashboardProps) {
  return (
    <div className="flex flex-col gap-6 rounded-lg border border-slate-800 bg-slate-950 p-5">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Shield className="h-5 w-5 text-indigo-400" />
        <h2 className="text-lg font-semibold text-slate-100">Privacy Dashboard</h2>
      </div>

      {/* Permissions table */}
      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-300">Agent Permissions</h3>
        <div className="overflow-hidden rounded-md border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900">
                <th className="px-4 py-2.5 text-left font-medium text-slate-400">
                  Agent
                </th>
                <th className="px-4 py-2.5 text-left font-medium text-slate-400">
                  Level
                </th>
                <th className="px-4 py-2.5 text-left font-medium text-slate-400">
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {permissions.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-slate-500">
                    No permissions data
                  </td>
                </tr>
              )}
              {permissions.map((perm, i) => (
                <tr
                  key={`${perm.agentName}-${i}`}
                  className="border-b border-slate-800/50 last:border-0"
                >
                  <td className="px-4 py-2.5 font-medium text-slate-200">
                    {perm.agentName}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                        LEVEL_COLORS[perm.level] ?? LEVEL_COLORS[0]
                      }`}
                    >
                      Level {perm.level}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-400">{perm.levelDescription}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit log */}
      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-300">Audit Log</h3>
        <div className="max-h-[400px] overflow-y-auto rounded-md border border-slate-800">
          <table className="w-full text-sm">
            <thead className="sticky top-0">
              <tr className="border-b border-slate-800 bg-slate-900">
                <th className="px-4 py-2.5 text-left font-medium text-slate-400">
                  Timestamp
                </th>
                <th className="px-4 py-2.5 text-left font-medium text-slate-400">
                  Action
                </th>
                <th className="px-4 py-2.5 text-left font-medium text-slate-400">
                  Category
                </th>
              </tr>
            </thead>
            <tbody>
              {auditLog.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-slate-500">
                    No audit entries
                  </td>
                </tr>
              )}
              {auditLog.map((entry, i) => (
                <tr
                  key={`${entry.timestamp}-${i}`}
                  className="border-b border-slate-800/50 last:border-0"
                >
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-400">
                    {entry.timestamp}
                  </td>
                  <td className="px-4 py-2.5 text-slate-200">{entry.action}</td>
                  <td className="px-4 py-2.5">
                    <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-400 border border-slate-700">
                      {entry.category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
