"use client";

import { ChatWorkspace } from "./chat-workspace";

export function TestAgentChat({ projectId }: { projectId: string }) {
  return <ChatWorkspace projectId={projectId} />;
}
