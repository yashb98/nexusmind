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
import { motion } from "framer-motion";

type Agent = Record<string, unknown>;

interface AgentPanelProps {
  agent: Agent;
  onTriggerConversation: (agentId?: string) => void;
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

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06, delayChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 320, damping: 28 } },
};

const tagVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1, transition: { type: "spring" as const, stiffness: 400, damping: 24 } },
};

export default function AgentPanel({ agent, onTriggerConversation }: AgentPanelProps) {
  const radarData = [
    { trait: "Openness", value: (agent.openness as number) || 0 },
    { trait: "Conscientiousness", value: (agent.conscientiousness as number) || 0 },
    { trait: "Extraversion", value: (agent.extraversion as number) || 0 },
    { trait: "Agreeableness", value: (agent.agreeableness as number) || 0 },
    { trait: "Neuroticism", value: (agent.neuroticism as number) || 0 },
  ];

  return (
    <motion.div
      className="flex flex-col gap-5 rounded-lg border border-slate-800 bg-slate-950 p-5"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div className="flex items-start justify-between" variants={itemVariants}>
        <motion.div
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 24, delay: 0.05 }}
        >
          <h2 className="text-lg font-semibold text-slate-100">{(agent.display_name as string) || "Agent"}</h2>
          <span className="mt-1 inline-block rounded-full border border-indigo-500/30 bg-indigo-500/20 px-2.5 py-0.5 text-xs font-medium text-indigo-400">
            {(agent.lora_archetype as string) || "Unknown"}
          </span>
        </motion.div>
      </motion.div>

      <motion.div variants={itemVariants}>
        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Communication Style</p>
        <p className="mt-1 text-sm text-slate-300">{(agent.communication_style as string) || "analytical"}</p>
      </motion.div>

      <motion.div variants={itemVariants}>
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">Big Five Personality</p>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="trait" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 1]} tick={{ fill: "#64748b", fontSize: 10 }} tickCount={5} />
              <Radar name="Traits" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      <motion.div variants={itemVariants}>
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">Interests</p>
        <ul className="flex flex-wrap gap-1.5 list-none p-0 m-0" aria-label="Agent interests">
          {((agent.interests as string[]) || []).map((interest, i) => (
            <motion.li key={interest} variants={tagVariants} custom={i} transition={{ delay: i * 0.05 }}>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${INTEREST_COLORS[i % INTEREST_COLORS.length]}`}>
                {interest}
              </span>
            </motion.li>
          ))}
        </ul>
      </motion.div>

      <motion.div variants={itemVariants}>
        <motion.button
          onClick={() => onTriggerConversation(agent.id as string)}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
        >
          <Play className="h-4 w-4" />
          Start Conversation
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
