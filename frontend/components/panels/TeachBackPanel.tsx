"use client";

import { useState } from "react";
import { Send, CheckCircle } from "lucide-react";

interface ChatMessage {
  id: string;
  role: "tutor" | "learner";
  content: string;
}

interface TeachBackPanelProps {
  sessionId: string;
  messages: ChatMessage[];
  bloomLevel: number; // 0-5 index
  onSend: (message: string) => void;
  onComplete: (sessionId: string) => void;
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
}: TeachBackPanelProps) {
  const [input, setInput] = useState("");

  function handleSend() {
    const text = input.trim();
    if (!text) return;
    onSend(text);
    setInput("");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex flex-col rounded-lg border border-slate-800 bg-slate-950 h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
        <h2 className="text-lg font-semibold text-slate-100">Teach-Back Session</h2>
        <button
          onClick={() => onComplete(sessionId)}
          className="flex items-center gap-1.5 rounded-md border border-green-500/30 bg-green-600/10 px-3 py-1.5 text-xs font-medium text-green-400 transition-colors hover:bg-green-600/20"
        >
          <CheckCircle className="h-3.5 w-3.5" />
          Complete
        </button>
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

      {/* Chat transcript */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="flex flex-col gap-3">
          {messages.map((msg) => (
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
        </div>
      </div>

      {/* Input */}
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
    </div>
  );
}
