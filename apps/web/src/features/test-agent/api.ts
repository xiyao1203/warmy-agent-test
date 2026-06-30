import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type ChatResponse = {
  session_id: string;
  messages: ChatMessage[];
  plan_draft: Record<string, unknown>;
  status: string;
};

export class TestAgentApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function sendChatMessage(
  projectId: string,
  message: string,
  sessionId?: string,
) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/test-agent/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify({ message, session_id: sessionId }),
    },
  );
  if (!res.ok) {
    const problem = await responseProblem(res, "测试 Agent 调用失败");
    throw new TestAgentApiError(problem.status, problem.message);
  }
  return res.json() as Promise<ChatResponse>;
}

export async function confirmPlan(projectId: string, sessionId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/test-agent/confirm`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify({ session_id: sessionId }),
    },
  );
  if (!res.ok) {
    const problem = await responseProblem(res, "确认测试计划失败");
    throw new TestAgentApiError(problem.status, problem.message);
  }
  return res.json() as Promise<{
    session_id: string;
    status: string;
    plan: Record<string, unknown>;
    message: string;
  }>;
}
