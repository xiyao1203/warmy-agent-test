import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export type ChatMessage = {
  message_id?: string;
  sequence?: number;
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

export type TargetChatTurn = {
  turn_id: string;
  sequence: number;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  trace: Array<Record<string, unknown>> | null;
  scores: Array<Record<string, unknown>> | null;
  duration_ms: number | null;
  token_usage: Record<string, unknown> | null;
  error: Record<string, unknown> | null;
  created_at: string;
};

export type TargetChatSession = {
  session_id: string;
  agent_version_id: string;
  environment_template_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  turns: TargetChatTurn[];
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

async function requestWithAbort<T>(url: string, init?: RequestInit & { signal?: AbortSignal }): Promise<T> {
  const { signal, ...rest } = init ?? {};
  const response = await fetch(url, { credentials: "include", ...rest, signal });
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

export function deleteSession(projectId: string, sessionId: string) {
  return fetch(`${base(projectId)}/sessions/${sessionId}`, {
    method: "DELETE",
    credentials: "include",
    headers: csrfHeaders() as Record<string, string>,
  });
}

export function sendChatMessage(
  projectId: string,
  sessionId: string,
  message: string,
  signal?: AbortSignal,
) {
  return requestWithAbort<ChatResponse>(
    `${base(projectId)}/sessions/${sessionId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      body: JSON.stringify({ message }),
      signal,
    },
  );
}

export function regenerateMessage(
  projectId: string,
  sessionId: string,
  editedMessage?: string,
  signal?: AbortSignal,
) {
  return requestWithAbort<ChatResponse>(
    `${base(projectId)}/sessions/${sessionId}/messages/regenerate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      body: JSON.stringify(
        editedMessage ? { message: editedMessage } : {},
      ),
      signal,
    },
  );
}

export function editMessage(
  projectId: string,
  sessionId: string,
  sequence: number,
  content: string,
) {
  return requestWithAbort<ChatResponse>(
    `${base(projectId)}/sessions/${sessionId}/messages/${sequence}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      body: JSON.stringify({ content }),
    },
  );
}

export function decideConfirmation(
  projectId: string,
  sessionId: string,
  confirmationId: string,
  approved: boolean,
) {
  return request<{
    task_id: string;
    status: string;
    output: Record<string, unknown> | null;
    error: Record<string, unknown> | null;
  }>(
    `${base(projectId)}/confirmations/${confirmationId}?session_id=${sessionId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      body: JSON.stringify({ approved }),
    },
  );
}

export function decideConfirmationsBatch(
  projectId: string,
  sessionId: string,
  confirmationIds: string[],
  approved: boolean,
) {
  return request<{
    results: {
      task_id: string;
      status: string;
      output: Record<string, unknown> | null;
      error: Record<string, unknown> | null;
    }[];
  }>(
    `${base(projectId)}/confirmations/batch?session_id=${sessionId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      body: JSON.stringify({ confirmation_ids: confirmationIds, approved }),
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
    "agent.reasoning",
    "agent.reasoning_delta",
    "agent.delegated",
    "agent.progress",
    "agent.completed",
    "agent.failed",
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

export function listTargetChats(projectId: string) {
  return request<{ items: TargetChatSession[] }>(
    `${base(projectId)}/target-chats`,
  );
}

export function createTargetChat(
  projectId: string,
  agentVersionId: string,
  environmentTemplateId?: string,
) {
  return request<TargetChatSession>(`${base(projectId)}/target-chats`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(csrfHeaders() as Record<string, string>),
    },
    body: JSON.stringify({
      agent_version_id: agentVersionId,
      environment_template_id: environmentTemplateId || null,
    }),
  });
}

export function sendTargetMessage(
  projectId: string,
  sessionId: string,
  message: string,
  signal?: AbortSignal,
) {
  return requestWithAbort<TargetChatTurn>(
    `${base(projectId)}/target-chats/${sessionId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      body: JSON.stringify({ message }),
      signal,
    },
  );
}
