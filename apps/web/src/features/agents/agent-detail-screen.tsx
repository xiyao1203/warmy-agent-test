"use client";

import { useQuery } from "@tanstack/react-query";

import {
  createAgentVersion,
  diffAgentVersions,
  publishAgentVersion,
  setBaselineAgentVersion,
  setCurrentAgentVersion,
  updateAgentVersion,
  updateAgent,
} from "./api";
import { AgentDetail } from "./agent-detail";
import { agentQueries } from "./queries";

export function AgentDetailScreen({
  agentId,
  projectId,
}: {
  agentId: string;
  projectId: string;
}) {
  const agentQuery = useQuery(agentQueries.detail(projectId, agentId));
  const versionsQuery = useQuery(agentQueries.versions(projectId, agentId));
  const relationshipsQuery = useQuery(
    agentQueries.relationships(projectId, agentId),
  );

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
        await Promise.all([refreshVersions(), agentQuery.refetch()]);
      }}
      onUpdateVersion={async (versionId, payload) => {
        await updateAgentVersion(projectId, agentId, versionId, payload);
        await refreshVersions();
      }}
      onSetCurrentVersion={async (versionId) => {
        await setCurrentAgentVersion(projectId, agentId, versionId);
        await agentQuery.refetch();
      }}
      onSetBaselineVersion={async (versionId) => {
        await setBaselineAgentVersion(projectId, agentId, versionId);
        await agentQuery.refetch();
      }}
      onFetchDiff={(v1, v2) => diffAgentVersions(projectId, agentId, v1, v2)}
      relationships={relationshipsQuery.data}
      onUpdateAgent={async (payload) => {
        await updateAgent(projectId, agentId, payload);
        await agentQuery.refetch();
      }}
      versions={versionsQuery.data}
    />
  );
}
