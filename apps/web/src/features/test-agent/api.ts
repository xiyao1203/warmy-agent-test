import { csrfHeaders } from "@/lib/api/csrf";

const API_BASE =
  process.env.NEXT_PUBLIC_CONTROL_API_URL ?? "http://localhost:8181";

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
  if (!res.ok) throw new Error("Failed to send message");
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
  if (!res.ok) throw new Error("Failed to confirm plan");
  return res.json() as Promise<{
    session_id: string;
    status: string;
    plan: Record<string, unknown>;
    message: string;
  }>;
}
