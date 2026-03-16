"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import { getInsights, getLearningProgress } from "@/lib/api";

interface Insight {
  id: string;
  text: string;
  topic?: string;
  verified: boolean;
}

interface TopicProgress {
  topic: string;
  bloom_level: number;
  sessions_completed: number;
}

const BLOOM_LABELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"];

export default function LearnPage() {
  const router = useRouter();
  const { token, _hydrated, myAgentId } = useStore();

  const [insights, setInsights] = useState<Insight[]>([]);
  const [progress, setProgress] = useState<TopicProgress[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!_hydrated) return;
    if (!token) { router.replace("/login"); return; }
    if (myAgentId) loadData();
  }, [token, _hydrated, myAgentId]);

  const loadData = async () => {
    if (!myAgentId) return;
    setLoading(true);
    try {
      const [insResp, progResp] = await Promise.all([
        getInsights(myAgentId).catch(() => ({ data: [] })),
        getLearningProgress(myAgentId).catch(() => ({ data: [] })),
      ]);
      setInsights(insResp.data);
      setProgress(progResp.data);
    } catch { /* handled */ }
    setLoading(false);
  };

  if (!_hydrated || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-gray-400">{!_hydrated ? "Loading..." : "Redirecting..."}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="text-xl font-bold mb-8">Learn</h1>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-600 border-t-purple-400" />
          </div>
        ) : insights.length === 0 && progress.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-20">Complete conversations to start learning.</p>
        ) : (
          <>
            {/* Learning Progress */}
            {progress.length > 0 && (
              <section className="mb-10">
                <h2 className="text-sm font-semibold text-gray-300 mb-4">Learning Progress</h2>
                <div className="space-y-3">
                  {progress.map((p) => (
                    <div key={p.topic} className="rounded-xl border border-gray-800 bg-gray-900 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white">{p.topic}</span>
                        <span className="text-xs text-purple-400">
                          {BLOOM_LABELS[Math.min(p.bloom_level, 5)]} (Level {p.bloom_level + 1}/6)
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-gray-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-purple-600 transition-all"
                          style={{ width: `${((p.bloom_level + 1) / 6) * 100}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{p.sessions_completed} sessions completed</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Teach Me */}
            {insights.length > 0 && (
              <section className="mb-10">
                <h2 className="text-sm font-semibold text-gray-300 mb-4">Teach Me</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {insights.slice(0, 20).map((ins) => (
                    <div key={ins.id} className="rounded-xl border border-gray-800 bg-gray-900 p-4 flex flex-col gap-2">
                      <p className="text-sm text-gray-300 line-clamp-3">{ins.text}</p>
                      <div className="flex items-center justify-between mt-auto pt-2">
                        {ins.topic && <span className="text-xs text-gray-500">{ins.topic}</span>}
                        <button className="rounded-lg bg-purple-600 px-3 py-1 text-xs font-medium text-white hover:bg-purple-500 transition-colors ml-auto">
                          Teach me
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Knowledge Map placeholder */}
            <section>
              <h2 className="text-sm font-semibold text-gray-300 mb-4">Knowledge Map</h2>
              <div className="rounded-xl border border-gray-800 bg-gray-900 p-12 text-center">
                <p className="text-sm text-gray-500">Interactive knowledge graph visualization coming soon.</p>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
