"use client";

import { Play } from "lucide-react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

type Agent = Record<string, unknown>;

interface AgentPanelProps {
  agent: Agent;
  onTriggerConversation: (agentId?: string) => void;
}

const TRAIT_COLORS: Record<string, string> = {
  analytical: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  creative: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  diplomatic: "bg-green-500/20 text-green-400 border-green-500/30",
  challenger: "bg-red-500/20 text-red-400 border-red-500/30",
  mentor: "bg-amber-500/20 text-amber-400 border-amber-500/30",
};

function archetypeStyle(archetype: string): string {
  const key = archetype.toLowerCase();
  return TRAIT_COLORS[key] ?? "bg-slate-500/20 text-slate-400 border-slate-500/30";
}

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

export default function AgentPanel({ agent, onTriggerConversation }: AgentPanelProps) {
  const radarData = [
    { trait: "Openness", value: (agent.openness as number) || 0 },
    { trait: "Conscientiousness", value: (agent.conscientiousness as number) || 0 },
    { trait: "Extraversion", value: (agent.extraversion as number) || 0 },
    { trait: "Agreeableness", value: (agent.agreeableness as number) || 0 },
    { trait: "Neuroticism", value: (agent.neuroticism as number) || 0 },
  ];

  return (
    <div className="flex flex-col gap-5 rounded-lg border border-slate-800 bg-slate-950 p-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{(agent.display_name as string) || "Agent"}</h2>
          <span
            className={`mt-1 inline-block rounded-full border px-2.5 py-0.5 text-xs font-medium ${archetypeStyle((agent.lora_archetype as string) || "")}`}
          >
            {(agent.lora_archetype as string) || "Unknown"}
          </span>
        </div>
      </div>

      {/* Communication style */}
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
          Communication Style
        </p>
        <p className="mt-1 text-sm text-slate-300">{(agent.communication_style as string) || "analytical"}</p>
      </div>

      {/* Big Five radar */}
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
          Big Five Personality Traits
        </p>
        <div className="h-56 w-full">
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
      </div>

      {/* Interests */}
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
          Interests
        </p>
        <div className="flex flex-wrap gap-1.5">
          {((agent.interests as string[]) || []).map((interest, i) => (
            <span
              key={interest}
              className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${INTEREST_COLORS[i % INTEREST_COLORS.length]}`}
            >
              {interest}
            </span>
          ))}
        </div>
      </div>

      {/* Action */}
      <button
        onClick={() => onTriggerConversation(agent.id as string)}
        className="flex items-center justify-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
      >
        <Play className="h-4 w-4" />
        Start Conversation
      </button>
    </div>
  );
}
