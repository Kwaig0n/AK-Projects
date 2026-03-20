import type { Agent, AgentCreate, AgentUpdate, Run, Finding, Skill } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Agents ───────────────────────────────────────────────────────────────────

export const api = {
  agents: {
    list: () => request<Agent[]>("/agents"),
    get: (id: number) => request<Agent>(`/agents/${id}`),
    create: (data: AgentCreate) =>
      request<Agent>("/agents", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: AgentUpdate) =>
      request<Agent>(`/agents/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number) =>
      request<void>(`/agents/${id}`, { method: "DELETE" }),
    run: (id: number) =>
      request<{ run_id: string; message: string }>(`/agents/${id}/run`, { method: "POST" }),
    toggle: (id: number) =>
      request<Agent>(`/agents/${id}/toggle`, { method: "POST" }),
  },

  runs: {
    list: (agentId?: number, limit = 50) => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (agentId) params.set("agent_id", String(agentId));
      return request<Run[]>(`/runs?${params}`);
    },
    get: (runId: string) => request<Run>(`/runs/${runId}`),
    stop: (runId: string) => request<{ message: string }>(`/runs/${runId}/stop`, { method: "POST" }),
    streamUrl: (runId: string) => `${BASE}/runs/${runId}/stream`,
  },

  findings: {
    list: (params?: {
      agent_id?: number;
      finding_type?: string;
      is_new?: boolean;
      min_score?: number;
      since_hours?: number;
      limit?: number;
    }) => {
      const q = new URLSearchParams();
      if (params?.agent_id) q.set("agent_id", String(params.agent_id));
      if (params?.finding_type) q.set("finding_type", params.finding_type);
      if (params?.is_new !== undefined) q.set("is_new", String(params.is_new));
      if (params?.min_score) q.set("min_score", String(params.min_score));
      if (params?.since_hours) q.set("since_hours", String(params.since_hours));
      if (params?.limit) q.set("limit", String(params.limit));
      return request<Finding[]>(`/findings?${q}`);
    },
    unreadCount: () => request<{ count: number }>("/findings/unread-count"),
    markRead: (id: number) =>
      request<Finding>(`/findings/${id}/read`, { method: "PUT" }),
    markAllRead: (agentId?: number) => {
      const q = agentId ? `?agent_id=${agentId}` : "";
      return request<{ count: number }>(`/findings/mark-all-read${q}`, { method: "POST" });
    },
  },

  skills: {
    list: () => request<Skill[]>("/agents/skills"),
  },

  health: () => request<{ status: string; environment: string; scheduled_jobs: number }>("/health"),
};
