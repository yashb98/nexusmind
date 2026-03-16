"use client";

import { useState, useRef, useEffect } from "react";
import { Send, CheckCircle, BookOpen, Sparkles } from "lucide-react";

interface ChatMessage {
  id: string;
  role: "tutor" | "learner";
  content: string;
}

interface InsightItem {
  id: string;
  text: string;
  verified: boolean;
  topic?: string;
}

interface TeachBackPanelProps {
  sessionId: string;
  messages: ChatMessage[];
  bloomLevel: number; // 0-5 index
  onSend: (message: string) => void;
  onComplete: (sessionId: string) => void;
  insights?: InsightItem[];
  onStartTeachback?: (insightId: string, insightText: string, topic: string) => void;
}

const BLOOM_LEVELS = [
  "Remember",
  "Understand",
  "Apply",
  "Analyze",
  "Evaluate",
  "Create",
];

const BLOOM_COLORS = [
  "bg-red-500",
  "bg-orange-500",
  "bg-yellow-500",
  "bg-lime-500",
  "bg-green-500",
  "bg-emerald-500",
];

export default function TeachBackPanel({
  sessionId,
  messages,
  bloomLevel,
  onSend,
  onComplete,
  insights,
  onStartTeachback,
}: TeachBackPanelProps) {
  const [input, setInput] = useState("");
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>(messages);
  const [activeInsightId, setActiveInsightId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Sync external messages into local state
  useEffect(() => {
    setLocalMessages(messages);
  }, [messages]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages]);

  const hasInsights = insights && insights.length > 0;
  const hasActiveSession = activeInsightId !== null || localMessages.length > 0;

  function handleSend() {
    const text = input.trim();
    if (!text) return;
    const newMsg: ChatMessage = {
      id: `learner-${Date.now()}`,
      role: "learner",
      content: text,
    };
    setLocalMessages((prev) => [...prev, newMsg]);
    onSend(text);
    setInput("");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleTeachMe(insight: InsightItem) {
    setActiveInsightId(insight.id);

    // Create mock tutor opening message
    const tutorMsg: ChatMessage = {
      id: `tutor-${Date.now()}`,
      role: "tutor",
      content: `Let's explore this insight together: "${insight.text}". What do you think this means? Try to explain it in your own words.`,
    };
    setLocalMessages([tutorMsg]);

    // Notify parent if callback is provided
    onStartTeachback?.(insight.id, insight.text, insight.topic || "general");
  }

  // ─── Empty state: no insights at all ────────────────────────────────────────
  if (!hasInsights) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center px-6">
        <BookOpen className="h-12 w-12 text-slate-700 mb-4" />
        <p className="text-slate-400 text-sm font-medium">
          Complete a conversation first to unlock the tutor.
        </p>
        <p className="text-slate-500 text-xs mt-2 max-w-xs leading-relaxed">
          Your AI tutor will help you understand what your agents discover.
          Start a Socratic debate, then come back here to learn from the insights.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col rounded-lg border border-slate-800 bg-slate-950 h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
        <h2 className="text-lg font-semibold text-slate-100">AI Tutor</h2>
        {hasActiveSession && (
          <button
            onClick={() => onComplete(sessionId)}
            className="flex items-center gap-1.5 rounded-md border border-green-500/30 bg-green-600/10 px-3 py-1.5 text-xs font-medium text-green-400 transition-colors hover:bg-green-600/20"
          >
            <CheckCircle className="h-3.5 w-3.5" />
            Complete
          </button>
        )}
      </div>

      {/* Bloom level progress */}
      <div className="border-b border-slate-800 px-5 py-3">
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
          Bloom Level
        </p>
        <div className="flex gap-1">
          {BLOOM_LEVELS.map((level, i) => (
            <div key={level} className="flex flex-1 flex-col items-center gap-1">
              <div
                className={`h-2 w-full rounded-full ${
                  i <= bloomLevel ? BLOOM_COLORS[i] : "bg-slate-800"
                }`}
              />
              <span
                className={`text-[9px] font-medium ${
                  i <= bloomLevel ? "text-slate-300" : "text-slate-600"
                }`}
              >
                {level}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Available insights (scrollable list) */}
      {!hasActiveSession && (
        <div className="border-b border-slate-800 px-5 py-3 max-h-[200px] overflow-y-auto">
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
            Available Insights
          </p>
          <div className="flex flex-col gap-2">
            {insights.map((insight) => (
              <div
                key={insight.id}
                className="flex items-start gap-2 rounded-md border border-slate-800 bg-slate-900 px-3 py-2.5"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    {insight.verified && (
                      <CheckCircle className="h-3 w-3 shrink-0 text-green-400" />
                    )}
                    {insight.topic && (
                      <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
                        {insight.topic}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {insight.text}
                  </p>
                </div>
                <button
                  onClick={() => handleTeachMe(insight)}
                  className="shrink-0 flex items-center gap-1 rounded-md border border-indigo-500/30 bg-indigo-600/10 px-2.5 py-1.5 text-xs font-medium text-indigo-400 transition-colors hover:bg-indigo-600/20"
                >
                  <Sparkles className="h-3 w-3" />
                  Teach me
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active insight indicator */}
      {hasActiveSession && activeInsightId && (
        <div className="border-b border-slate-800 px-5 py-2 bg-indigo-600/5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-medium uppercase tracking-wider text-indigo-400">
              Exploring insight
            </span>
            <button
              onClick={() => {
                setActiveInsightId(null);
                setLocalMessages([]);
              }}
              className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
            >
              Choose another
            </button>
          </div>
        </div>
      )}

      {/* Chat transcript */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!hasActiveSession && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <p className="text-slate-500 text-sm">
              Choose an insight above to start learning with your tutor.
            </p>
          </div>
        )}
        {hasActiveSession && (
          <div className="flex flex-col gap-3">
            {localMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col gap-0.5 max-w-[85%] ${
                  msg.role === "learner" ? "self-end items-end" : "self-start items-start"
                }`}
              >
                <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
                  {msg.role === "tutor" ? "Tutor" : "You"}
                </span>
                <div
                  className={`rounded-lg px-3.5 py-2.5 text-sm leading-relaxed ${
                    msg.role === "learner"
                      ? "bg-indigo-600/20 text-slate-200 border border-indigo-500/30"
                      : "bg-slate-800 text-slate-300 border border-slate-700"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      {hasActiveSession && (
        <div className="border-t border-slate-800 px-4 py-3">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your response..."
              className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="flex items-center justify-center rounded-md bg-indigo-600 p-2 text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
