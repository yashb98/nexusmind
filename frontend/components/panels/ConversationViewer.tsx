"use client";

import { CheckCircle } from "lucide-react";

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
}

const PHASE_STYLES: Record<Phase, string> = {
  OPEN: "bg-blue-500/20 text-blue-400 border-blue-500/40",
  PROBE: "bg-purple-500/20 text-purple-400 border-purple-500/40",
  DEEPEN: "bg-indigo-500/20 text-indigo-400 border-indigo-500/40",
  CHALLENGE: "bg-red-500/20 text-red-400 border-red-500/40",
  SYNTHESIZE: "bg-green-500/20 text-green-400 border-green-500/40",
  EXTRACT: "bg-amber-500/20 text-amber-400 border-amber-500/40",
};

function QualityBadge({ score }: { score: number }) {
  let color = "bg-red-500/20 text-red-400 border-red-500/40";
  if (score >= 0.8) color = "bg-green-500/20 text-green-400 border-green-500/40";
  else if (score >= 0.5) color = "bg-yellow-500/20 text-yellow-400 border-yellow-500/40";

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${color}`}>
      Quality: {(score * 100).toFixed(0)}%
    </span>
  );
}

export default function ConversationViewer({
  messages,
  insights,
  qualityScore,
}: ConversationViewerProps) {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-slate-800 bg-slate-950 p-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Conversation</h2>
        {qualityScore !== undefined && <QualityBadge score={qualityScore} />}
      </div>

      {/* Messages */}
      <div className="flex flex-col gap-3 max-h-[500px] overflow-y-auto pr-1">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col gap-1 max-w-[80%] ${
              msg.side === "right" ? "self-end items-end" : "self-start items-start"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-400">{msg.speaker}</span>
              <span
                className={`rounded-full border px-2 py-px text-[10px] font-semibold uppercase ${PHASE_STYLES[msg.phase]}`}
              >
                {msg.phase}
              </span>
            </div>
            <div
              className={`rounded-lg px-3.5 py-2.5 text-sm leading-relaxed ${
                msg.side === "right"
                  ? "bg-indigo-600/20 text-slate-200 border border-indigo-500/30"
                  : "bg-slate-800 text-slate-300 border border-slate-700"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {/* Insights */}
      {insights && insights.length > 0 && (
        <div className="border-t border-slate-800 pt-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-300">Extracted Insights</h3>
          <div className="flex flex-col gap-2">
            {insights.map((insight) => (
              <div
                key={insight.id}
                className="flex items-start gap-2 rounded-md border border-slate-800 bg-slate-900 px-3 py-2"
              >
                {insight.verified && (
                  <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-green-400" />
                )}
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm text-slate-300">{insight.text}</span>
                  {insight.topic && (
                    <span className="text-xs text-slate-500">{insight.topic}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
