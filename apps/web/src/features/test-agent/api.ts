import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type ArtifactLink = {
  type: string;
  id: string;
  relation: string;
};

export type SessionSummary = {
  session_id: string;
  title: string;
  status: string;
  updated_at: string;
};

export type ChatResponse = SessionSummary & {
  messages: ChatMessage[];
  artifacts: ArtifactLink[];
  protocol_version: number;
  plan_draft: Record<string, unknown>;
};

export type AgentEvent = {
  id: number;
  type: string;
  payload: Record<string, unknown>;
};

export class TestAgentApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { credentials: "include", ...init });
  if (!response.ok) {
    const problem = await responseProblem(response, "测试 Agent 调用失败");
    throw new TestAgentApiError(problem.status, problem.message);
  }
  return response.json() as Promise<T>;
}

const base = (projectId: string) =>
  `${API_BASE}/api/v1/projects/${projectId}/test-agent`;

export function listSessions(projectId: string) {
  return request<{ items: SessionSummary[] }>(`${base(projectId)}/sessions`);
}

export function createSession(projectId: string) {
  return request<ChatResponse>(`${base(projectId)}/sessions`, {
    method: "POST",
    headers: csrfHeaders() as Record<string, string>,
  });
}

export function getSession(projectId: string, sessionId: string) {
  return request<ChatResponse>(`${base(projectId)}/sessions/${sessionId}`);
}

export function sendChatMessage(
  projectId: string,
  sessionId: string,
  message: string,
) {
  return request<ChatResponse>(
    `${base(projectId)}/sessions/${sessionId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      body: JSON.stringify({ message }),
    },
  );
}

export function subscribeToSession(
  projectId: string,
  sessionId: string,
  onEvent: (event: AgentEvent) => void,
  onError?: () => void,
) {
  const source = new EventSource(
    `${base(projectId)}/sessions/${sessionId}/events`,
    { withCredentials: true },
  );
  const eventTypes = [
    "message.started",
    "message.delta",
    "message.completed",
    "agent.delegated",
    "agent.progress",
    "agent.completed",
    "tool.confirmation_required",
    "asset.created",
    "asset.updated",
    "run.progress",
    "run.completed",
    "error",
  ];
  for (const type of eventTypes) {
    source.addEventListener(type, (raw) => {
      const message = raw as MessageEvent<string>;
      onEvent({
        id: Number(message.lastEventId || 0),
        type,
        payload: JSON.parse(message.data) as Record<string, unknown>,
      });
    });
  }
  source.onerror = () => onError?.();
  return () => source.close();
}
