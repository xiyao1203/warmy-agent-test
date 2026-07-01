"use client";

import { useQuery } from "@tanstack/react-query";

import {
  createAgentVersion,
  getAgent,
  listAgentVersions,
  publishAgentVersion,
  updateAgentVersion,
} from "./api";
import { AgentDetail } from "./agent-detail";

export function AgentDetailScreen({
  agentId,
  projectId,
}: {
  agentId: string;
  projectId: string;
}) {
  const agentQuery = useQuery({
    queryFn: () => getAgent(projectId, agentId),
    queryKey: ["agent", projectId, agentId],
  });
  const versionsQuery = useQuery({
    queryFn: () => listAgentVersions(projectId, agentId),
    queryKey: ["agent-versions", projectId, agentId],
  });

  if (agentQuery.isPending || versionsQuery.isPending) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        正在加载 Agent 详情…
      </div>
    );
  }
  if (agentQuery.isError || versionsQuery.isError) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
        <div>
          <h1 className="text-base font-semibold">Agent 不存在或你无权访问</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            请返回 Agent 列表检查项目和资源地址。
          </p>
        </div>
      </div>
    );
  }

  async function refreshVersions() {
    await versionsQuery.refetch();
  }

  return (
    <AgentDetail
      agent={agentQuery.data}
      onCreateVersion={async (payload) => {
        await createAgentVersion(projectId, agentId, payload);
        await refreshVersions();
      }}
      onPublish={async (versionId) => {
        await publishAgentVersion(projectId, agentId, versionId);
        await refreshVersions();
      }}
      onUpdateVersion={async (versionId, payload) => {
        await updateAgentVersion(projectId, agentId, versionId, payload);
        await refreshVersions();
      }}
      versions={versionsQuery.data}
    />
  );
}
