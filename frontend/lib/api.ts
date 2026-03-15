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

// Onboarding
export const getScenarios = () => api.get("/api/v1/onboarding/scenarios");
export const scorePersonality = (answers: { question_id: number; option_index: number }[]) =>
  api.post("/api/v1/onboarding/personality", { answers });

// Agents
export const createAgent = (data: Record<string, unknown>) => api.post("/api/v1/agents", data);
export const listAgents = () => api.get("/api/v1/agents");
export const getAgent = (id: string) => api.get(`/api/v1/agents/${id}`);

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
