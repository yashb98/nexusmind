import { create } from "zustand";
import { useEffect } from "react";

interface AppState {
  token: string | null;
  userId: string | null;
  tenantId: string | null;
  myAgentId: string | null;
  selectedAgentId: string | null;
  selectedConversation: Record<string, unknown> | null;
  activePanel: string;
  _hydrated: boolean;

  setToken: (token: string) => void;
  setUser: (userId: string, tenantId: string) => void;
  setMyAgentId: (agentId: string) => void;
  selectAgent: (agentId: string | null) => void;
  selectConversation: (conv: Record<string, unknown> | null) => void;
  setActivePanel: (panel: string) => void;
  logout: () => void;
  _hydrate: () => void;
}

export const useStore = create<AppState>((set) => ({
  token: null,
  userId: null,
  tenantId: null,
  myAgentId: null,
  selectedAgentId: null,
  selectedConversation: null,
  activePanel: "agent",
  _hydrated: false,

  setToken: (token) => {
    if (typeof window !== "undefined") localStorage.setItem("token", token);
    set({ token });
  },

  setUser: (userId, tenantId) => set({ userId, tenantId }),

  setMyAgentId: (agentId) => {
    if (typeof window !== "undefined") localStorage.setItem("my_agent_id", agentId);
    set({ myAgentId: agentId });
  },

  selectAgent: (agentId) => set({ selectedAgentId: agentId, activePanel: "agent" }),

  selectConversation: (conv) => set({ selectedConversation: conv, activePanel: "conversation" }),

  setActivePanel: (panel) => set({ activePanel: panel }),

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("my_agent_id");
    }
    set({ token: null, userId: null, tenantId: null, myAgentId: null });
  },

  _hydrate: () => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("token");
      const myAgentId = localStorage.getItem("my_agent_id");
      set({ token, myAgentId, _hydrated: true });
    }
  },
}));

/** Call this once in your root layout or top-level component. */
export function useHydrateStore() {
  const hydrate = useStore((s) => s._hydrate);
  const hydrated = useStore((s) => s._hydrated);
  useEffect(() => {
    if (!hydrated) hydrate();
  }, [hydrate, hydrated]);
}
