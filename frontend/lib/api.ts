import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// JWT interceptor
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Auth
export const register = (email: string, displayName: string, password: string) =>
  api.post("/api/v1/auth/register", { email, display_name: displayName, password });

export const login = (email: string, password: string) =>
  api.post("/api/v1/auth/login", { email, password });

export const getMe = () => api.get("/api/v1/auth/me");
export const updateMe = (data: { display_name?: string }) =>
  api.patch("/api/v1/auth/me", data);

// Onboarding
export const getScenarios = () => api.get("/api/v1/onboarding/scenarios");
export const scorePersonality = (answers: { question_id: number | string; option_index: number }[]) =>
  api.post("/api/v1/onboarding/personality", { answers });
export const getAdaptiveQuestions = (interests: string[]) =>
  api.get(`/api/v1/onboarding/questions?interests=${interests.join(",")}`);
export const scoreAdaptivePersonality = (
  answers: { question_id: number | string; option_index: number }[],
  questions: Record<string, unknown>[],
) => api.post("/api/v1/onboarding/personality/adaptive", { answers, questions });

// Agents
export const createAgent = (data: Record<string, unknown>) => api.post("/api/v1/agents", data);
export const listAgents = () => api.get("/api/v1/agents");
export const getAgent = (id: string) => api.get(`/api/v1/agents/${id}`);
export const updateAgent = (id: string, data: Record<string, unknown>) =>
  api.patch(`/api/v1/agents/${id}`, data);

// Graph
export const getNetwork = (agentId: string, hops = 3) =>
  api.get(`/api/v1/graph/agents/${agentId}/network?hops=${hops}`);
export const getRecommendations = (agentId: string) =>
  api.get(`/api/v1/graph/agents/${agentId}/recommendations`);
export const getCommunities = () => api.get("/api/v1/graph/communities");
export const getTrendingTopics = () => api.get("/api/v1/graph/topics/trending");
export const detectCommunities = () => api.post("/api/v1/graph/communities/detect");

// Conversations
export const triggerConversation = (agentAId: string, agentBId: string, topic: string) =>
  api.post("/api/v1/conversations", { agent_a_id: agentAId, agent_b_id: agentBId, topic });
export const broadcastConversation = (agentId: string, topic: string) =>
  api.post("/api/v1/conversations/broadcast", { agent_id: agentId, topic });

/** Stream a Socratic debate turn-by-turn via SSE. */
export function streamConversation(
  agentAId: string,
  agentBId: string,
  topic: string,
  onMeta: (meta: Record<string, unknown>) => void,
  onTurn: (turn: Record<string, unknown>) => void,
  onDone: (result: Record<string, unknown>) => void,
  onError: (err: string) => void,
): () => void {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const controller = new AbortController();

  fetch(`${API_URL}/api/v1/conversations/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ agent_a_id: agentAId, agent_b_id: agentBId, topic }),
    signal: controller.signal,
  })
    .then(async (resp) => {
      if (!resp.ok) { onError(`HTTP ${resp.status}`); return; }
      const reader = resp.body?.getReader();
      if (!reader) return;
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          const dataLine = line.replace(/^data: /, "").trim();
          if (!dataLine) continue;
          try {
            const event = JSON.parse(dataLine);
            if (event.type === "meta") onMeta(event);
            else if (event.type === "turn") onTurn(event);
            else if (event.type === "done") onDone(event);
          } catch { /* ignore */ }
        }
      }
    })
    .catch((err) => { if (err.name !== "AbortError") onError(String(err)); });

  return () => controller.abort();
}

// Insights
export const getInsights = (agentId: string) => api.get(`/api/v1/agents/${agentId}/insights`);
export const getDiscoveries = (agentId: string) => api.get(`/api/v1/agents/${agentId}/discoveries`);

// Verification
export const getRecentVerifications = () => api.get("/api/v1/verification/recent");

// Teach-back
export const startTeachback = (insightId: string, insightContent: string, topic: string) =>
  api.post("/api/v1/teachback/start", { insight_id: insightId, insight_content: insightContent, topic });
export const respondTeachback = (sessionId: string, message: string) =>
  api.post(`/api/v1/teachback/${sessionId}/respond`, { message });
export const completeTeachback = (sessionId: string) =>
  api.post(`/api/v1/teachback/${sessionId}/complete`);

// Permissions
export const getPermissions = (agentId: string) => api.get(`/api/v1/agents/${agentId}/permissions`);
export const getAuditLog = (agentId: string) => api.get(`/api/v1/agents/${agentId}/audit`);

// Scheduler
export const getSchedulerStatus = () => api.get("/api/v1/scheduler/status");
export const pauseScheduler = () => api.post("/api/v1/scheduler/pause");
export const resumeScheduler = () => api.post("/api/v1/scheduler/resume");

// Evolution
export const getProposals = () => api.get("/api/v1/evolution/proposals");
export const getFinetuneHistory = () => api.get("/api/v1/evolution/finetune/history");
export const getEvolutionMetrics = () => api.get("/api/v1/evolution/metrics");

// Avatar
export const getAvatarPresets = () => api.get("/api/v1/avatar/presets");

export default api;
