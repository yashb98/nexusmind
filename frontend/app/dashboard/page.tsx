"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import { listAgents, getNetwork, getInsights, getSchedulerStatus } from "@/lib/api";
import dynamic from "next/dynamic";
import AgentPanel from "@/components/panels/AgentPanel";
import ConversationViewer from "@/components/panels/ConversationViewer";
import InsightsFeed from "@/components/panels/InsightsFeed";
import TeachBackPanel from "@/components/panels/TeachBackPanel";
import PrivacyDashboard from "@/components/panels/PrivacyDashboard";
import EvolutionDashboard from "@/components/panels/EvolutionDashboard";

const GraphView = dynamic(() => import("@/components/graph/GraphView"), { ssr: false });

const TABS = [
  { id: "agent", label: "Agent" },
  { id: "conversation", label: "Conversation" },
  { id: "insights", label: "Insights" },
  { id: "teachback", label: "Teach-Back" },
  { id: "privacy", label: "Privacy" },
  { id: "evolution", label: "Evolution" },
];

export default function DashboardPage() {
  const router = useRouter();
  const { activePanel, setActivePanel, selectAgent, selectedAgentId, token, _hydrated } = useStore();
  const [agents, setAgents] = useState<Record<string, unknown>[]>([]);
  const [graphData, setGraphData] = useState<{ nodes: { id: string; [k: string]: unknown }[]; edges: { source: string; target: string; [k: string]: unknown }[] }>({ nodes: [], edges: [] });
  const [insights, setInsights] = useState<Record<string, unknown>[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (!_hydrated) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    loadData();
  }, [token, _hydrated]);

  useEffect(() => {
    if (selectedAgentId) {
      loadAgentData(selectedAgentId);
    }
  }, [selectedAgentId]);

  const loadData = async () => {
    try {
      const [agentsResp, statusResp] = await Promise.all([
        listAgents(),
        getSchedulerStatus().catch(() => ({ data: {} })),
      ]);
      setAgents(agentsResp.data);
      setSchedulerStatus(statusResp.data);

      if (agentsResp.data.length > 0) {
        const firstAgent = agentsResp.data[0];
        selectAgent(firstAgent.id);
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

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) as Record<string, unknown> | undefined;

  if (!_hydrated || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-gray-400">{!_hydrated ? "Loading..." : "Redirecting..."}</div>
      </div>
    );
  }

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
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph panel (60%) */}
        <div className="w-3/5 border-r border-gray-800">
          <GraphView
            nodes={graphData.nodes}
            edges={graphData.edges}
            onNodeClick={(nodeId: string) => selectAgent(nodeId)}
            onEdgeClick={() => setActivePanel("conversation")}
          />
        </div>

        {/* Side panel (40%) */}
        <div className="w-2/5 flex flex-col">
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
            {activePanel === "agent" && selectedAgent && (
              <AgentPanel
                agent={selectedAgent}
                onTriggerConversation={() => setActivePanel("conversation")}
              />
            )}
            {activePanel === "conversation" && <ConversationViewer messages={[] as any} insights={[] as any} qualityScore={0} />}
            {activePanel === "insights" && (
              <InsightsFeed
                insights={insights as any}
                onTeachMe={() => setActivePanel("teachback")}
              />
            )}
            {activePanel === "teachback" && (
              <TeachBackPanel
                sessionId={"" as any}
                messages={[]}
                bloomLevel={1}
                onSend={() => {}}
                onComplete={() => {}}
              />
            )}
            {activePanel === "privacy" && (
              <PrivacyDashboard permissions={[] as any} auditLog={[] as any} />
            )}
            {activePanel === "evolution" && (
              <EvolutionDashboard
                schedulerStatus={schedulerStatus as any}
                finetuneHistory={[] as any}
                proposals={[] as any}
                metrics={{} as any}
              />
            )}
            {!selectedAgent && activePanel === "agent" && (
              <div className="text-gray-500 text-center mt-20">
                Select an agent from the graph to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
