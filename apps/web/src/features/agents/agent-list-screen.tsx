"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { problemKind } from "@/lib/api/problem";

import { createAgent, deleteAgent, listAgents } from "./api";
import { AgentList } from "./agent-list";

export function AgentListScreen({ projectId }: { projectId: string }) {
  const router = useRouter();
  const agentsQuery = useQuery({
    queryFn: () => listAgents(projectId),
    queryKey: ["agents", projectId],
  });

  if (agentsQuery.isPending) {
    return <AgentList loading projectId={projectId} />;
  }
  if (agentsQuery.isError) {
    const kind = problemKind(agentsQuery.error);
    return (
      <AgentList
        error={
          kind === "not-found" || kind === "permission"
            ? "not-found"
            : "service"
        }
        projectId={projectId}
      />
    );
  }
  return (
    <AgentList
      agents={agentsQuery.data.items}
      onCreate={async (payload) => {
        const created = await createAgent(projectId, payload);
        router.push(`/projects/${projectId}/agents/${created.id}`);
      }}
      onDelete={async (agentId) => {
        await deleteAgent(projectId, agentId);
        await agentsQuery.refetch();
      }}
      projectId={projectId}
    />
  );
}
