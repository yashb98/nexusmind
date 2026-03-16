"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, X, Plus, Trash2 } from "lucide-react";
import { useStore } from "@/lib/store";
import { getMe, updateMe, getAgent, updateAgent } from "@/lib/api";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

// ─── Types ───────────────────────────────────────────────────────────────────

interface UserInfo {
  id: string;
  email: string;
  display_name: string;
  tenant_id: string;
  role: string;
}

interface AgentInfo {
  id: string;
  display_name: string;
  communication_style: string;
  default_privacy_level: number;
  interests: string[];
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  lora_archetype: string | null;
  [key: string]: unknown;
}

const COMM_STYLES = ["analytical", "expressive", "driver", "amiable"];

const PRIVACY_LEVELS = [
  { value: 1, label: "Open", desc: "Anyone in tenant can view" },
  { value: 2, label: "Standard", desc: "Shared with connections" },
  { value: 3, label: "Private", desc: "Only you and your agent" },
  { value: 4, label: "Locked", desc: "Maximum privacy" },
];

const ARCHETYPE_COLORS: Record<string, string> = {
  analytical: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  creative: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  diplomatic: "bg-green-500/20 text-green-400 border-green-500/30",
  challenger: "bg-red-500/20 text-red-400 border-red-500/30",
  mentor: "bg-amber-500/20 text-amber-400 border-amber-500/30",
};

const INTEREST_COLORS = [
  "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  "bg-pink-500/20 text-pink-300 border-pink-500/30",
  "bg-lime-500/20 text-lime-300 border-lime-500/30",
  "bg-orange-500/20 text-orange-300 border-orange-500/30",
  "bg-violet-500/20 text-violet-300 border-violet-500/30",
  "bg-teal-500/20 text-teal-300 border-teal-500/30",
  "bg-rose-500/20 text-rose-300 border-rose-500/30",
  "bg-sky-500/20 text-sky-300 border-sky-500/30",
];

// ─── Profile Page ────────────────────────────────────────────────────────────

export default function ProfilePage() {
  const router = useRouter();
  const { token, _hydrated, myAgentId, logout } = useStore();

  const [user, setUser] = useState<UserInfo | null>(null);
  const [agent, setAgent] = useState<AgentInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // User form state
  const [displayName, setDisplayName] = useState("");
  const [userSaving, setUserSaving] = useState(false);
  const [userMsg, setUserMsg] = useState("");

  // Agent form state
  const [agentName, setAgentName] = useState("");
  const [commStyle, setCommStyle] = useState("analytical");
  const [privacyLevel, setPrivacyLevel] = useState(2);
  const [interests, setInterests] = useState<string[]>([]);
  const [newInterest, setNewInterest] = useState("");
  const [agentSaving, setAgentSaving] = useState(false);
  const [agentMsg, setAgentMsg] = useState("");

  // Delete confirmation
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Auth guard
  useEffect(() => {
    if (!_hydrated) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    loadProfile();
  }, [token, _hydrated]);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    try {
      const [meResp, agentResp] = await Promise.all([
        getMe(),
        myAgentId ? getAgent(myAgentId) : Promise.resolve(null),
      ]);
      const u = meResp.data as UserInfo;
      setUser(u);
      setDisplayName(u.display_name);

      if (agentResp) {
        const a = agentResp.data as AgentInfo;
        setAgent(a);
        setAgentName(a.display_name);
        setCommStyle(a.communication_style);
        setPrivacyLevel(a.default_privacy_level);
        setInterests([...a.interests]);
      }
    } catch (err) {
      console.error("Failed to load profile:", err);
    } finally {
      setLoading(false);
    }
  }, [myAgentId]);

  // ─── Handlers ──────────────────────────────────────────────────────────────

  const handleSaveUser = async () => {
    if (!displayName.trim()) return;
    setUserSaving(true);
    setUserMsg("");
    try {
      const resp = await updateMe({ display_name: displayName.trim() });
      setUser(resp.data as UserInfo);
      setUserMsg("Saved");
      setTimeout(() => setUserMsg(""), 2000);
    } catch {
      setUserMsg("Failed to save");
    } finally {
      setUserSaving(false);
    }
  };

  const handleSaveAgent = async () => {
    if (!agent) return;
    setAgentSaving(true);
    setAgentMsg("");
    try {
      const resp = await updateAgent(agent.id, {
        display_name: agentName.trim() || undefined,
        communication_style: commStyle,
        default_privacy_level: privacyLevel,
        interests: interests.length > 0 ? interests : undefined,
      });
      setAgent(resp.data as AgentInfo);
      setAgentMsg("Saved");
      setTimeout(() => setAgentMsg(""), 2000);
    } catch {
      setAgentMsg("Failed to save");
    } finally {
      setAgentSaving(false);
    }
  };

  const addInterest = () => {
    const trimmed = newInterest.trim();
    if (trimmed && !interests.includes(trimmed) && interests.length < 10) {
      setInterests([...interests, trimmed]);
      setNewInterest("");
    }
  };

  const removeInterest = (interest: string) => {
    setInterests(interests.filter((i) => i !== interest));
  };

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  // ─── Loading / Guard ───────────────────────────────────────────────────────

  if (!_hydrated || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-gray-400">
          {!_hydrated ? "Loading..." : "Redirecting..."}
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" />
      </div>
    );
  }

  // Radar chart data
  const radarData = agent
    ? [
        { trait: "Openness", value: agent.openness },
        { trait: "Conscientiousness", value: agent.conscientiousness },
        { trait: "Extraversion", value: agent.extraversion },
        { trait: "Agreeableness", value: agent.agreeableness },
        { trait: "Neuroticism", value: agent.neuroticism },
      ]
    : [];

  const archetypeStyle =
    ARCHETYPE_COLORS[(agent?.lora_archetype || "").toLowerCase()] ??
    "bg-slate-500/20 text-slate-400 border-slate-500/30";

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Top bar */}
      <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center px-6">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Dashboard
        </Link>
        <h1 className="ml-4 text-lg font-bold">Profile</h1>
      </header>

      <div className="mx-auto max-w-2xl px-4 py-8 space-y-6">
        {/* ─── Section 1: User Info ─────────────────────────────────────── */}
        <section className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-base font-semibold text-slate-100 mb-4">
            User Info
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 mb-1">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 mb-1">
                Email
              </label>
              <input
                type="email"
                value={user?.email || ""}
                readOnly
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-slate-400 text-sm cursor-not-allowed"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleSaveUser}
                disabled={userSaving || displayName.trim() === user?.display_name}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {userSaving ? "Saving..." : "Save"}
              </button>
              {userMsg && (
                <span className={`text-sm ${userMsg === "Saved" ? "text-green-400" : "text-red-400"}`}>
                  {userMsg}
                </span>
              )}
            </div>
          </div>
        </section>

        {/* ─── Section 2: Agent Settings ────────────────────────────────── */}
        {agent && (
          <section className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <h2 className="text-base font-semibold text-slate-100 mb-4">
              Agent Settings
            </h2>
            <div className="space-y-4">
              {/* Agent name */}
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 mb-1">
                  Agent Name
                </label>
                <input
                  type="text"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
                />
              </div>

              {/* Communication style */}
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 mb-1">
                  Communication Style
                </label>
                <select
                  value={commStyle}
                  onChange={(e) => setCommStyle(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500 text-sm"
                >
                  {COMM_STYLES.map((s) => (
                    <option key={s} value={s}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Privacy level */}
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
                  Privacy Level
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {PRIVACY_LEVELS.map((lvl) => (
                    <button
                      key={lvl.value}
                      onClick={() => setPrivacyLevel(lvl.value)}
                      className={`rounded-lg border px-3 py-2.5 text-left transition-colors ${
                        privacyLevel === lvl.value
                          ? "border-indigo-500 bg-indigo-600/20"
                          : "border-gray-700 hover:border-gray-600 hover:bg-gray-800"
                      }`}
                    >
                      <span className="text-sm font-medium text-slate-200">
                        {lvl.label}
                      </span>
                      <span className="block text-xs text-slate-500 mt-0.5">
                        {lvl.desc}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Interests */}
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
                  Interests
                </label>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {interests.map((interest, i) => (
                    <span
                      key={interest}
                      className={`flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${INTEREST_COLORS[i % INTEREST_COLORS.length]}`}
                    >
                      {interest}
                      <button
                        onClick={() => removeInterest(interest)}
                        className="hover:opacity-70"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
                {interests.length < 10 && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newInterest}
                      onChange={(e) => setNewInterest(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addInterest()}
                      placeholder="Add interest..."
                      className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
                    />
                    <button
                      onClick={addInterest}
                      disabled={!newInterest.trim()}
                      className="flex items-center gap-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-slate-300 hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add
                    </button>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleSaveAgent}
                  disabled={agentSaving}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {agentSaving ? "Saving..." : "Save Agent"}
                </button>
                {agentMsg && (
                  <span className={`text-sm ${agentMsg === "Saved" ? "text-green-400" : "text-red-400"}`}>
                    {agentMsg}
                  </span>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ─── Section 3: Personality (Read-only) ───────────────────────── */}
        {agent && radarData.length > 0 && (
          <section className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-100">
                Personality
              </h2>
              {agent.lora_archetype && (
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${archetypeStyle}`}
                >
                  {agent.lora_archetype}
                </span>
              )}
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis
                    dataKey="trait"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 1]}
                    tick={{ fill: "#64748b", fontSize: 10 }}
                    tickCount={5}
                  />
                  <Radar
                    name="Traits"
                    dataKey="value"
                    stroke="#6366f1"
                    fill="#6366f1"
                    fillOpacity={0.25}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              These are set during onboarding and reflect your cognitive style.
            </p>
          </section>
        )}

        {/* ─── Section 4: Account Actions ───────────────────────────────── */}
        <section className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-base font-semibold text-slate-100 mb-4">
            Account
          </h2>
          <div className="flex flex-col gap-3">
            <button
              onClick={handleLogout}
              className="w-full py-2.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Log Out
            </button>
            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-red-950/30 hover:bg-red-950/50 border border-red-900/30 text-red-400 rounded-lg text-sm font-medium transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                Delete Account
              </button>
            ) : (
              <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
                <p className="text-sm text-red-300 mb-3">
                  Are you sure? This action cannot be undone. All your data, agent, and
                  conversation history will be permanently deleted.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    disabled
                    className="flex-1 py-2 bg-red-900/50 border border-red-800/50 text-red-400 rounded-lg text-sm font-medium cursor-not-allowed opacity-50"
                    title="Not yet implemented"
                  >
                    Confirm Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
