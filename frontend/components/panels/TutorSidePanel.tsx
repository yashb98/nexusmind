"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronRight, ChevronLeft, GraduationCap } from "lucide-react";

export interface TutorMessage {
  mode: string;
  content: string;
  turn: number;
}

interface TutorSidePanelProps {
  messages: TutorMessage[];
}

const MODE_BADGES: Record<string, { label: string; icon: string }> = {
  explain: { label: "Explain", icon: "\uD83D\uDCA1" },
  check: { label: "Check", icon: "\uD83E\uDD14" },
  reflect: { label: "Reflect", icon: "\uD83E\uDE9E" },
  observe: { label: "Observe", icon: "\uD83D\uDC40" },
};

export default function TutorSidePanel({ messages }: TutorSidePanelProps) {
  const [minimized, setMinimized] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  if (minimized) {
    return (
      <div className="flex flex-col items-center pt-4">
        <button
          onClick={() => setMinimized(false)}
          className="flex items-center gap-1 rounded-lg border border-amber-700/30 bg-amber-900/20 px-2 py-2 text-amber-300 hover:bg-amber-900/40 transition-colors"
          title="Expand tutor panel"
        >
          <ChevronLeft className="h-4 w-4" />
          <GraduationCap className="h-4 w-4" />
          {messages.length > 0 && (
            <span className="ml-1 text-xs font-medium">{messages.length}</span>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full border-l border-slate-800 bg-slate-950/50">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-slate-800 shrink-0">
        <div className="flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-amber-300">Tutor</h3>
          <span className="text-xs text-slate-500">{messages.length} notes</span>
        </div>
        <button
          onClick={() => setMinimized(true)}
          className="text-slate-500 hover:text-slate-300 transition-colors"
          title="Minimize tutor panel"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 flex flex-col gap-2.5 scroll-smooth"
      >
        {messages.length === 0 && (
          <p className="text-xs text-slate-600 text-center mt-8">
            Tutor commentary will appear here as the debate progresses.
          </p>
        )}
        {messages.map((msg, i) => {
          const badge = MODE_BADGES[msg.mode] || MODE_BADGES.observe;
          return (
            <div
              key={i}
              className="rounded-lg bg-amber-900/20 border border-amber-700/30 px-3 py-2 text-sm animate-in fade-in slide-in-from-right-2 duration-300"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-amber-800/50 text-amber-300">
                  {badge.icon} {badge.label}
                </span>
                <span className="text-xs text-gray-500">Turn {msg.turn}</span>
              </div>
              <p className="text-amber-200/80 leading-relaxed">{msg.content}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
