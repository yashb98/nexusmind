"use client";

import { useEffect, useRef } from "react";
import { CheckCircle } from "lucide-react";
import TutorSidePanel, { TutorMessage } from "./TutorSidePanel";
import { motion } from "framer-motion";

type Phase = "OPEN" | "PROBE" | "DEEPEN" | "CHALLENGE" | "SYNTHESIZE" | "EXTRACT";

interface Message {
  id: string;
  speaker: string;
  content: string;
  phase: Phase;
  side: "left" | "right";
}

interface Insight {
  id: string;
  text: string;
  verified: boolean;
  topic?: string;
}

interface ConversationViewerProps {
  messages: Message[];
  insights?: Insight[];
  qualityScore?: number;
  mode?: string;
  tutorMessages?: TutorMessage[];
}

const MODE_LABELS: Record<string, { label: string; icon: string }> = {
  socratic: { label: "Socratic Debate", icon: "⚡" },
  casual: { label: "Casual Chat", icon: "💬" },
  brainstorm: { label: "Brainstorm", icon: "💡" },
  teach: { label: "Teach", icon: "📚" },
  research: { label: "Research", icon: "🔬" },
  play: { label: "Play", icon: "🎮" },
  project: { label: "Project", icon: "🛠" },
  reflection: { label: "Reflection", icon: "🪞" },
};

const PHASE_STYLES: Record<Phase, string> = {
  OPEN: "bg-blue-500/20 text-blue-400 border-blue-500/40",
  PROBE: "bg-purple-500/20 text-purple-400 border-purple-500/40",
  DEEPEN: "bg-indigo-500/20 text-indigo-400 border-indigo-500/40",
  CHALLENGE: "bg-red-500/20 text-red-400 border-red-500/40",
  SYNTHESIZE: "bg-green-500/20 text-green-400 border-green-500/40",
  EXTRACT: "bg-amber-500/20 text-amber-400 border-amber-500/40",
};

function renderContent(raw: string) {
  const paragraphs = raw.split(/\n{2,}/);
  return paragraphs.map((para, pi) => {
    const parts: (string | { type: "em" | "strong" | "code"; text: string })[] = [];
    const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
    let lastIndex = 0;
    let match;
    while ((match = regex.exec(para)) !== null) {
      if (match.index > lastIndex) parts.push(para.slice(lastIndex, match.index));
      if (match[2]) parts.push({ type: "strong", text: match[2] });
      else if (match[3]) parts.push({ type: "em", text: match[3] });
      else if (match[4]) parts.push({ type: "code", text: match[4] });
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < para.length) parts.push(para.slice(lastIndex));
    return (
      <p key={pi} className={pi > 0 ? "mt-2" : ""}>
        {parts.map((part, i) => {
          if (typeof part === "string") return <span key={i}>{part}</span>;
          if (part.type === "strong") return <strong key={i} className="font-semibold text-slate-100">{part.text}</strong>;
          if (part.type === "em") return <em key={i} className="italic text-slate-400">{part.text}</em>;
          if (part.type === "code") return <code key={i} className="rounded bg-slate-700/50 px-1 py-0.5 text-xs font-mono text-indigo-300">{part.text}</code>;
          return null;
        })}
      </p>
    );
  });
}

function QualityBadge({ score }: { score: number }) {
  const pct = Math.min(100, (score / 10) * 100);
  let color = "bg-red-500/20 text-red-400 border-red-500/40";
  let label = "Low";
  if (pct >= 80) { color = "bg-green-500/20 text-green-400 border-green-500/40"; label = "High"; }
  else if (pct >= 50) { color = "bg-yellow-500/20 text-yellow-400 border-yellow-500/40"; label = "Medium"; }
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${color}`} aria-label={`Quality: ${label} at ${pct.toFixed(0)} percent`}>
      {label} — {pct.toFixed(0)}%
    </span>
  );
}

const messageVariants = {
  hidden: (side: "left" | "right") => ({ opacity: 0, x: side === "right" ? 24 : -24 }),
  visible: { opacity: 1, x: 0, transition: { type: "spring" as const, stiffness: 300, damping: 28 } },
};

export default function ConversationViewer({ messages, insights, qualityScore, mode, tutorMessages }: ConversationViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const hasTutor = tutorMessages && tutorMessages.length > 0;

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages.length]);

  return (
    <div className="flex flex-col gap-4 rounded-lg border border-slate-800 bg-slate-950 p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-slate-100">Conversation</h2>
          {mode && MODE_LABELS[mode] && (
            <span className="inline-flex items-center gap-1 rounded-full border border-purple-500/40 bg-purple-500/20 px-2.5 py-0.5 text-xs font-medium text-purple-400">
              {MODE_LABELS[mode].icon} {MODE_LABELS[mode].label}
            </span>
          )}
        </div>
        {qualityScore !== undefined && qualityScore > 0 && <QualityBadge score={qualityScore} />}
      </div>

      <div className={`flex ${hasTutor ? "gap-0" : ""}`}>
        <div className={hasTutor ? "w-[60%] min-w-0" : "w-full"}>
          <ul ref={scrollRef} role="log" aria-live="polite" aria-label="Conversation messages" className="flex flex-col gap-3 max-h-[500px] overflow-y-auto pr-1 scroll-smooth list-none">
            {messages.map((msg, index) => (
              <motion.li
                key={msg.id}
                custom={msg.side}
                variants={messageVariants}
                initial="hidden"
                animate="visible"
                transition={{ delay: index * 0.04 }}
                className={`flex flex-col gap-1 max-w-[85%] ${msg.side === "right" ? "self-end items-end" : "self-start items-start"}`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-300">{msg.speaker}</span>
                  <span className={`rounded-full border px-2 py-px text-[10px] font-semibold uppercase ${PHASE_STYLES[msg.phase] || PHASE_STYLES.OPEN}`}>
                    {msg.phase}
                  </span>
                </div>
                <div className={`rounded-lg px-3.5 py-2.5 text-sm leading-relaxed ${msg.side === "right" ? "bg-indigo-600/20 text-slate-200 border border-indigo-500/30" : "bg-slate-800 text-slate-300 border border-slate-700"}`}>
                  {renderContent(msg.content)}
                </div>
              </motion.li>
            ))}
          </ul>
        </div>
        {hasTutor && (
          <div className="w-[40%] min-w-0 max-h-[500px]">
            <TutorSidePanel messages={tutorMessages} />
          </div>
        )}
      </div>

      {insights && insights.length > 0 && (
        <div className="border-t border-slate-800 pt-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-300">Extracted Insights</h3>
          <div className="flex flex-col gap-2">
            {insights.map((insight) => (
              <div key={insight.id} className="flex items-start gap-2 rounded-md border border-slate-800 bg-slate-900 px-3 py-2">
                {insight.verified && <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-green-400" aria-label="Verified" />}
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm text-slate-300">{insight.text}</span>
                  {insight.topic && <span className="text-xs text-slate-500">{insight.topic}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
