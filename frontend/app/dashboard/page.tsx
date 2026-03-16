"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import {
  listAgents,
  getNetwork,
  getInsights,
  getSchedulerStatus,
  streamConversation,
} from "@/lib/api";
import dynamic from "next/dynamic";
import { Play, X, MessageSquare } from "lucide-react";
import Link from "next/link";
import AgentPanel from "@/components/panels/AgentPanel";
import ConversationViewer from "@/components/panels/ConversationViewer";
import InsightsFeed from "@/components/panels/InsightsFeed";
import TeachBackPanel from "@/components/panels/TeachBackPanel";
import PrivacyDashboard from "@/components/panels/PrivacyDashboard";
import EvolutionDashboard from "@/components/panels/EvolutionDashboard";

const GraphView = dynamic(() => import("@/components/graph/GraphView"), {
  ssr: false,
});

const TABS = [
  { id: "agent", label: "Agent" },
  { id: "conversation", label: "Conversation" },
  { id: "insights", label: "Insights" },
  { id: "teachback", label: "Teach Me" },
  { id: "privacy", label: "Privacy" },
  { id: "evolution", label: "Evolution" },
];

// ─── Conversation Picker Modal ───────────────────────────────────────────────

const CONVERSATION_MODES = [
  { id: "socratic", label: "Socratic Debate", icon: "\u26A1", description: "Structured intellectual debate with phases" },
  { id: "casual", label: "Casual Chat", icon: "\uD83D\uDCAC", description: "Natural conversation to build trust" },
  { id: "brainstorm", label: "Brainstorm", icon: "\uD83D\uDCA1", description: "Collaborative idea generation" },
  { id: "teach", label: "Teach", icon: "\uD83D\uDCDA", description: "One agent explains to another" },
  { id: "research", label: "Research", icon: "\uD83D\uDD2C", description: "Collaborative investigation" },
  { id: "play", label: "Play", icon: "\uD83C\uDFAE", description: "Games and fun interactions" },
  { id: "project", label: "Project", icon: "\uD83D\uDEE0", description: "Goal-oriented collaboration" },
  { id: "reflection", label: "Reflection", icon: "\uD83E\uDE9E", description: "Thinking out loud with a listener" },
] as const;

type ConversationMode = typeof CONVERSATION_MODES[number]["id"];

interface PickerProps {
  agents: Record<string, unknown>[];
  myAgentId: string;
  onStart: (partnerId: string, topic: string, mode: ConversationMode) => void;
  onClose: () => void;
}

function ConversationPicker({ agents, myAgentId, onStart, onClose }: PickerProps) {
  const [selectedPartner, setSelectedPartner] = useState<string | null>(null);
  const [topic, setTopic] = useState("");
  const [selectedMode, setSelectedMode] = useState<ConversationMode>("socratic");
  const others = agents.filter((a) => a.id !== myAgentId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Start a Conversation</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="text-sm text-slate-400 mb-3">Choose an agent to debate with:</p>
        <div className="max-h-48 overflow-y-auto flex flex-col gap-1.5 mb-4">
          {others.map((a) => (
            <button
              key={a.id as string}
              onClick={() => setSelectedPartner(a.id as string)}
              className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors ${
                selectedPartner === a.id
                  ? "border-indigo-500 bg-indigo-600/20"
                  : "border-slate-700 hover:border-slate-600 hover:bg-slate-800"
              }`}
            >
              <div className="flex-1">
                <span className="text-sm font-medium text-slate-200">
                  {a.display_name as string}
                </span>
                <span className="ml-2 text-xs text-slate-500">
                  {a.lora_archetype as string}
                </span>
              </div>
              {a.is_mock && (
                <span className="text-[10px] bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded">
                  AI
                </span>
              )}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="Enter a debate topic..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500 mb-4"
        />

        <div className="mb-4">
          <label className="text-sm text-gray-400">Conversation Mode</label>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {CONVERSATION_MODES.map((mode) => (
              <button
                key={mode.id}
                onClick={() => setSelectedMode(mode.id)}
                className={`rounded-lg border p-2.5 text-left transition-colors ${
                  selectedMode === mode.id
                    ? "border-purple-500 bg-purple-900/20"
                    : "border-gray-700 hover:border-gray-500"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-base">{mode.icon}</span>
                  <span className="text-sm font-medium text-gray-200">{mode.label}</span>
                </div>
                <p className="mt-0.5 text-xs text-gray-500">{mode.description}</p>
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={() => selectedPartner && topic.trim() && onStart(selectedPartner, topic.trim(), selectedMode)}
          disabled={!selectedPartner || !topic.trim()}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <MessageSquare className="h-4 w-4" />
          Start Conversation
        </button>
      </div>
    </div>
  );
}

// ─── Dashboard Page ──────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const {
    activePanel,
    setActivePanel,
    selectAgent,
    selectedAgentId,
    token,
    _hydrated,
    myAgentId,
  } = useStore();

  const [agents, setAgents] = useState<Record<string, unknown>[]>([]);
  const [graphData, setGraphData] = useState<{
    nodes: { id: string; [k: string]: unknown }[];
    edges: { source: string; target: string; [k: string]: unknown }[];
  }>({ nodes: [], edges: [] });
  const [insights, setInsights] = useState<Record<string, unknown>[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<Record<string, unknown>>({});
  const [showPicker, setShowPicker] = useState(false);
  const [graphWidth, setGraphWidth] = useState(60); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const [convMode, setConvMode] = useState<string>("socratic");
  const [convMeta, setConvMeta] = useState<{ agent_a: { name: string }; agent_b: { name: string }; topic: string; mode?: string } | null>(null);
  const [liveMessages, setLiveMessages] = useState<{ id: string; speaker: string; content: string; phase: string; side: "left" | "right" }[]>([]);
  const [convResult, setConvResult] = useState<{ quality_score: number; insights: { content: string; importance: number }[] } | null>(null);
  const [conversationLoading, setConversationLoading] = useState(false);
  const [tutorMessages, setTutorMessages] = useState<{mode: string; content: string; turn: number}[]>([]);

  useEffect(() => {
    if (!_hydrated) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    loadData();
  }, [token, _hydrated]);

  useEffect(() => {
    const agentForGraph = myAgentId || selectedAgentId;
    if (agentForGraph) {
      loadAgentData(agentForGraph);
    }
  }, [myAgentId, selectedAgentId]);

  // Resizable divider drag handling
  useEffect(() => {
    if (!isDragging) return;
    const onMouseMove = (e: MouseEvent) => {
      const pct = (e.clientX / window.innerWidth) * 100;
      setGraphWidth(Math.min(85, Math.max(25, pct)));
    };
    const onMouseUp = () => setIsDragging(false);
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging]);

  const loadData = async () => {
    try {
      const [agentsResp, statusResp] = await Promise.all([
        listAgents(),
        getSchedulerStatus().catch(() => ({ data: {} })),
      ]);
      setAgents(agentsResp.data);
      setSchedulerStatus(statusResp.data);

      // BUG 2 FIX: Select the user's OWN agent, not the first in the list
      if (myAgentId) {
        selectAgent(myAgentId);
      } else {
        // Fallback: pick the first non-mock agent
        const myAgent = agentsResp.data.find((a: Record<string, unknown>) => !a.is_mock);
        if (myAgent) {
          selectAgent(myAgent.id as string);
        } else if (agentsResp.data.length > 0) {
          selectAgent(agentsResp.data[0].id as string);
        }
      }
    } catch (err) {
      console.error("Failed to load data:", err);
    }
  };

  const loadAgentData = async (agentId: string) => {
    try {
      const [networkResp, insightsResp] = await Promise.all([
        getNetwork(agentId).catch(() => ({ data: { nodes: [], edges: [] } })),
        getInsights(agentId).catch(() => ({ data: [] })),
      ]);
      setGraphData(networkResp.data);
      setInsights(insightsResp.data);
    } catch (err) {
      console.error("Failed to load agent data:", err);
    }
  };

  // Stream conversation turn-by-turn
  const handleStartConversation = useCallback(
    (partnerId: string, topic: string, mode: string = "socratic") => {
      if (!myAgentId) return;
      setShowPicker(false);
      setLiveMessages([]);
      setTutorMessages([]);
      setConvMeta(null);
      setConvResult(null);
      setConvMode(mode);
      setConversationLoading(true);
      setActivePanel("conversation");

      streamConversation(
        myAgentId,
        partnerId,
        topic,
        mode,
        // onMeta
        (meta) => {
          setConvMeta(meta as any);
        },
        // onTurn — append each message as it arrives
        (turn) => {
          setLiveMessages((prev) => [
            ...prev,
            {
              id: String(turn.turn),
              speaker: turn.speaker as string,
              content: turn.content as string,
              phase: turn.phase as string,
              side: turn.side as "left" | "right",
            },
          ]);
        },
        // onDone — conversation finished, reload insights + graph
        (result) => {
          setConvResult(result as any);
          setConversationLoading(false);
          // Refresh insights and graph now that new data exists
          const agentForRefresh = myAgentId || selectedAgentId;
          if (agentForRefresh) loadAgentData(agentForRefresh);
        },
        // onError
        (err) => {
          console.error("Stream error:", err);
          setConversationLoading(false);
        },
        // onTutor — append tutor commentary as it arrives
        (tutor) => {
          setTutorMessages((prev) => [
            ...prev,
            {
              mode: tutor.mode as string,
              content: tutor.content as string,
              turn: tutor.turn as number,
            },
          ]);
        },
      );
    },
    [myAgentId, setActivePanel],
  );

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) as
    | Record<string, unknown>
    | undefined;

  const myAgent = agents.find((a) => a.id === myAgentId) as
    | Record<string, unknown>
    | undefined;

  if (!_hydrated || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-gray-400">
          {!_hydrated ? "Loading..." : "Redirecting..."}
        </div>
      </div>
    );
  }

  // Build insights from streaming result
  const convInsights = (convResult?.insights ?? []).map(
    (ins, i) => ({
      id: String(i),
      text: ins.content,
      verified: false,
      topic: convMeta?.topic,
    }),
  );

  return (
    <div className="h-screen bg-gray-950 text-white flex flex-col">
      {/* Top bar */}
      <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center px-6 justify-between shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold">NexusMind</h1>
          <span className="text-sm text-gray-400">{agents.length} agents</span>
          {Boolean(schedulerStatus.running) && (
            <span className="text-xs bg-green-900 text-green-300 px-2 py-0.5 rounded-full">
              Scheduler Active
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {myAgent && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span className="text-slate-300 font-medium">
                {myAgent.display_name as string}
              </span>
              <span className="text-xs bg-indigo-900/50 text-indigo-300 px-2 py-0.5 rounded-full">
                {myAgent.lora_archetype as string}
              </span>
            </div>
          )}
          <Link
            href="/profile"
            className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors"
            title="Profile"
          >
            {(myAgent?.display_name as string)?.charAt(0)?.toUpperCase() || "U"}
          </Link>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph panel */}
        <div style={{ width: `${graphWidth}%` }} className="shrink-0">
          <GraphView
            nodes={graphData.nodes}
            edges={graphData.edges}
            onNodeClick={(nodeId: string) => selectAgent(nodeId)}
            onEdgeClick={() => setActivePanel("conversation")}
          />
        </div>

        {/* Draggable divider */}
        <div
          onMouseDown={() => setIsDragging(true)}
          className={`w-1 shrink-0 cursor-col-resize transition-colors hover:bg-indigo-500 ${isDragging ? "bg-indigo-500" : "bg-gray-800"}`}
        />

        {/* Side panel */}
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Tab bar */}
          <div className="flex border-b border-gray-800 bg-gray-900 shrink-0">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActivePanel(tab.id)}
                className={`px-4 py-2.5 text-sm transition-colors ${
                  activePanel === tab.id
                    ? "text-blue-400 border-b-2 border-blue-400"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Panel content */}
          <div className="flex-1 overflow-y-auto p-4">
            {/* Agent panel */}
            {activePanel === "agent" && selectedAgent && (
              <AgentPanel
                agent={selectedAgent}
                onTriggerConversation={() => setShowPicker(true)}
              />
            )}
            {activePanel === "agent" && !selectedAgent && (
              <div className="text-gray-500 text-center mt-20">
                Select an agent from the graph to view details
              </div>
            )}

            {/* Conversation panel — live streaming */}
            {activePanel === "conversation" && (
              <>
                {liveMessages.length > 0 && (
                  <>
                    {convMeta && (
                      <div className="mb-3 flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h2 className="text-sm font-semibold text-slate-200">
                              {convMeta.agent_a.name} vs {convMeta.agent_b.name}
                            </h2>
                            <span className="inline-flex items-center gap-1 rounded-full border border-purple-500/40 bg-purple-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase text-purple-400">
                              {CONVERSATION_MODES.find((m) => m.id === (convMeta.mode || convMode))?.icon}{" "}
                              {CONVERSATION_MODES.find((m) => m.id === (convMeta.mode || convMode))?.label || convMode}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500">Topic: {convMeta.topic}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {conversationLoading && (
                            <>
                              <div className="h-3 w-3 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" />
                              <span className="text-xs text-slate-500">Live — Turn {liveMessages.length}/10</span>
                            </>
                          )}
                          {convResult && !conversationLoading && (
                            <>
                              <span className="text-xs bg-green-900/50 text-green-400 px-2 py-0.5 rounded-full">
                                Complete — Quality {Math.min(100, (convResult.quality_score / 10) * 100).toFixed(0)}%
                              </span>
                              {convResult.insights.length > 0 && (
                                <span className="text-xs bg-indigo-900/50 text-indigo-300 px-2 py-0.5 rounded-full">
                                  {convResult.insights.length} insights
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    )}
                    <ConversationViewer
                      messages={liveMessages as any}
                      insights={!conversationLoading ? (convInsights as any) : []}
                      qualityScore={convResult?.quality_score}
                      mode={convMeta?.mode || convMode}
                      tutorMessages={tutorMessages.length > 0 ? tutorMessages : undefined}
                    />
                  </>
                )}
                {liveMessages.length === 0 && !conversationLoading && (
                  <div className="flex flex-col items-center justify-center py-20 text-center">
                    <MessageSquare className="h-10 w-10 text-slate-700 mb-3" />
                    <p className="text-slate-400 text-sm">No conversations yet.</p>
                    <p className="text-slate-500 text-xs mt-1">
                      Click &quot;Start Conversation&quot; on the Agent tab to begin your first Socratic debate.
                    </p>
                    <button
                      onClick={() => setShowPicker(true)}
                      className="mt-4 flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
                    >
                      <Play className="h-4 w-4" />
                      Start Conversation
                    </button>
                  </div>
                )}
                {liveMessages.length === 0 && conversationLoading && (
                  <div className="flex flex-col items-center justify-center py-20">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" />
                    <p className="mt-3 text-sm text-slate-400">Connecting to debate...</p>
                  </div>
                )}
              </>
            )}

            {/* Insights panel */}
            {activePanel === "insights" && (
              <InsightsFeed
                insights={insights as any}
                onTeachMe={() => setActivePanel("teachback")}
              />
            )}

            {/* Teach-Back panel */}
            {activePanel === "teachback" && (
              <TeachBackPanel
                sessionId={"" as any}
                messages={[]}
                bloomLevel={1}
                onSend={() => {}}
                onComplete={() => {}}
                insights={
                  (convInsights.length > 0
                    ? convInsights
                    : (insights as { id: string; text: string; verified: boolean; topic?: string }[])
                  ) as any
                }
                onStartTeachback={(id, text, topic) => {
                  /* TODO: call startTeachback API */
                }}
              />
            )}

            {/* Privacy panel */}
            {activePanel === "privacy" && (
              <PrivacyDashboard
                permissions={[] as any}
                auditLog={[] as any}
              />
            )}

            {/* Evolution panel */}
            {activePanel === "evolution" && (
              <EvolutionDashboard
                schedulerStatus={schedulerStatus as any}
                finetuneHistory={[] as any}
                proposals={[] as any}
                metrics={{} as any}
              />
            )}
          </div>
        </div>
      </div>

      {/* Conversation Picker Modal — BUG 3 FIX */}
      {showPicker && myAgentId && (
        <ConversationPicker
          agents={agents}
          myAgentId={myAgentId}
          onStart={handleStartConversation}
          onClose={() => setShowPicker(false)}
        />
      )}
    </div>
  );
}
