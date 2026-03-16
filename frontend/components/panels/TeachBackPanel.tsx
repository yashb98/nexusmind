"use client";

import { useState, useRef, useEffect } from "react";
import { Send, CheckCircle, BookOpen, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ChatMessage { id: string; role: "tutor" | "learner"; content: string; }
interface InsightItem { id: string; text: string; verified: boolean; topic?: string; }

interface TeachBackPanelProps {
  sessionId: string;
  messages: ChatMessage[];
  bloomLevel: number;
  onSend: (message: string) => void;
  onComplete: (sessionId: string) => void;
  insights?: InsightItem[];
  onStartTeachback?: (insightId: string, insightText: string, topic: string) => void;
}

const BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"];
const BLOOM_COLORS = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-lime-500", "bg-green-500", "bg-emerald-500"];

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3.5 py-2.5 rounded-lg bg-slate-800 border border-slate-700 self-start max-w-[4rem]">
      {[0, 1, 2].map((i) => (
        <motion.span key={i} className="block h-1.5 w-1.5 rounded-full bg-slate-400" animate={{ y: [0, -4, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15, ease: "easeInOut" }} />
      ))}
    </div>
  );
}

export default function TeachBackPanel({ sessionId, messages, bloomLevel, onSend, onComplete, insights, onStartTeachback }: TeachBackPanelProps) {
  const [input, setInput] = useState("");
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>(messages);
  const [activeInsightId, setActiveInsightId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setLocalMessages(messages); }, [messages]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [localMessages, isTyping]);

  const hasInsights = insights && insights.length > 0;
  const hasActiveSession = activeInsightId !== null || localMessages.length > 0;

  function handleSend() {
    const text = input.trim();
    if (!text) return;
    setLocalMessages((prev) => [...prev, { id: `learner-${Date.now()}`, role: "learner", content: text }]);
    onSend(text);
    setInput("");
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 1800);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }

  function handleTeachMe(insight: InsightItem) {
    setActiveInsightId(insight.id);
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setLocalMessages([{
        id: `tutor-${Date.now()}`,
        role: "tutor",
        content: `Let's explore this insight together: "${insight.text}". What do you think this means? Try to explain it in your own words.`,
      }]);
    }, 1200);
    onStartTeachback?.(insight.id, insight.text, insight.topic || "general");
  }

  if (!hasInsights) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center px-6">
        <BookOpen className="h-12 w-12 text-slate-700 mb-4" />
        <p className="text-slate-400 text-sm font-medium">Complete a conversation first to unlock the tutor.</p>
        <p className="text-slate-500 text-xs mt-2 max-w-xs leading-relaxed">
          Your AI tutor will help you understand what your agents discover. Start a Socratic debate, then come back here to learn from the insights.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col rounded-lg border border-slate-800 bg-slate-950 h-full">
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
        <h2 className="text-lg font-semibold text-slate-100">AI Tutor</h2>
        {hasActiveSession && (
          <button onClick={() => onComplete(sessionId)} className="flex items-center gap-1.5 rounded-md border border-green-500/30 bg-green-600/10 px-3 py-1.5 text-xs font-medium text-green-400 transition-colors hover:bg-green-600/20">
            <CheckCircle className="h-3.5 w-3.5" /> Complete
          </button>
        )}
      </div>

      <div className="border-b border-slate-800 px-5 py-3">
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">Bloom Level</p>
        <div className="flex gap-1">
          {BLOOM_LEVELS.map((level, i) => (
            <div key={level} className="flex flex-1 flex-col items-center gap-1">
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <motion.div className={`h-full rounded-full ${i <= bloomLevel ? BLOOM_COLORS[i] : "bg-transparent"}`} initial={{ width: 0 }} animate={{ width: i <= bloomLevel ? "100%" : "0%" }} transition={{ type: "spring", stiffness: 120, damping: 20, delay: i * 0.08 }} />
              </div>
              <span className={`text-[9px] font-medium ${i <= bloomLevel ? "text-slate-300" : "text-slate-600"}`}>{level}</span>
            </div>
          ))}
        </div>
      </div>

      {!hasActiveSession && (
        <div className="border-b border-slate-800 px-5 py-3 max-h-[200px] overflow-y-auto">
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">Available Insights</p>
          <div className="flex flex-col gap-2">
            {insights?.map((insight) => (
              <div key={insight.id} className="flex items-start gap-2 rounded-md border border-slate-800 bg-slate-900 px-3 py-2.5">
                <div className="flex-1 min-w-0">
                  {insight.verified && <CheckCircle className="h-3 w-3 inline text-green-400 mr-1" />}
                  {insight.topic && <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{insight.topic} — </span>}
                  <p className="text-sm text-slate-300 leading-relaxed inline">{insight.text}</p>
                </div>
                <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => handleTeachMe(insight)} aria-label={`Teach me about: ${insight.text.slice(0, 60)}`} className="shrink-0 flex items-center gap-1 rounded-md border border-indigo-500/30 bg-indigo-600/10 px-2.5 py-1.5 text-xs font-medium text-indigo-400 transition-colors hover:bg-indigo-600/20">
                  <Sparkles className="h-3 w-3" /> Teach me
                </motion.button>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasActiveSession && activeInsightId && (
        <div className="border-b border-slate-800 px-5 py-2 bg-indigo-600/5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-medium uppercase tracking-wider text-indigo-400">Exploring insight</span>
            <button onClick={() => { setActiveInsightId(null); setLocalMessages([]); }} className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors">Choose another</button>
          </div>
        </div>
      )}

      <div role="log" aria-live="polite" aria-label="Tutor chat messages" className="flex-1 overflow-y-auto px-5 py-4">
        {!hasActiveSession && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <p className="text-slate-500 text-sm">Choose an insight above to start learning with your tutor.</p>
          </div>
        )}
        {hasActiveSession && (
          <div className="flex flex-col gap-3">
            <AnimatePresence initial={false}>
              {localMessages.map((msg) => (
                <motion.div key={msg.id} initial={{ opacity: 0, x: msg.role === "learner" ? 24 : -24, y: 8 }} animate={{ opacity: 1, x: 0, y: 0 }} transition={{ duration: 0.25, ease: "easeOut" }} className={`flex flex-col gap-0.5 max-w-[85%] ${msg.role === "learner" ? "self-end items-end" : "self-start items-start"}`}>
                  <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">{msg.role === "tutor" ? "Tutor" : "You"}</span>
                  <div className={`rounded-lg px-3.5 py-2.5 text-sm leading-relaxed ${msg.role === "learner" ? "bg-indigo-600/20 text-slate-200 border border-indigo-500/30" : "bg-slate-800 text-slate-300 border border-slate-700"}`}>{msg.content}</div>
                </motion.div>
              ))}
            </AnimatePresence>
            {isTyping && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="self-start">
                <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500 mb-1 block">Tutor</span>
                <TypingIndicator />
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {hasActiveSession && (
        <div className="border-t border-slate-800 px-4 py-3">
          <div className="flex items-center gap-2">
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Type your response..." aria-label="Your response to the tutor" className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500" />
            <button onClick={handleSend} disabled={!input.trim()} aria-label="Send message" className="flex items-center justify-center rounded-md bg-indigo-600 p-2 text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed">
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
