"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { problemKind } from "@/lib/api/problem";
import { usePaginationState } from "@/lib/use-pagination-state";

import { createAgent, deleteAgent } from "./api";
import { AgentList } from "./agent-list";
import { agentQueries, invalidateAgentList } from "./queries";

export function AgentListScreen({ projectId }: { projectId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const pagination = usePaginationState();
  const agentsQuery = useQuery(
    agentQueries.list(projectId, pagination.page, pagination.pageSize),
  );

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
        await invalidateAgentList(queryClient, projectId);
      }}
      onPageChange={pagination.setPage}
      onPageSizeChange={pagination.setPageSize}
      page={agentsQuery.data.page ?? pagination.page}
      pageSize={pagination.pageSize}
      projectId={projectId}
      total={agentsQuery.data.total}
      totalPages={agentsQuery.data.total_pages}
    />
  );
}
