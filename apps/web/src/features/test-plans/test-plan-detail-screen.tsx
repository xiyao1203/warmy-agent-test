"use client";

import { useQuery } from "@tanstack/react-query";

import { listAgentVersions, listAgents } from "@/features/agents";
import { listDatasets, listDatasetVersions } from "@/features/datasets";

import {
  createTestPlanVersion,
  getTestPlan,
  listEnvironmentTemplates,
  listTestPlanVersions,
  publishTestPlanVersion,
  updateTestPlanVersion,
} from "./api";
import { TestPlanDetail } from "./test-plan-detail";
import type { VersionAssetOption } from "./test-plan-version-dialog";

export function TestPlanDetailScreen({
  planId,
  projectId,
}: {
  planId: string;
  projectId: string;
}) {
  const planQuery = useQuery({
    queryFn: () => getTestPlan(projectId, planId),
    queryKey: ["test-plan", projectId, planId],
  });
  const versionsQuery = useQuery({
    queryFn: () => listTestPlanVersions(projectId, planId),
    queryKey: ["test-plan-versions", projectId, planId],
  });
  const assetsQuery = useQuery({
    queryFn: () => loadAssetOptions(projectId),
    queryKey: ["test-plan-assets", projectId],
  });
  if (
    planQuery.isPending ||
    versionsQuery.isPending ||
    assetsQuery.isPending
  ) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        正在加载测试计划详情…
      </div>
    );
  }
  if (planQuery.isError || versionsQuery.isError || assetsQuery.isError) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
        <div>
          <h1 className="text-base font-semibold">
            测试计划不存在或你无权访问
          </h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            请返回测试计划列表检查项目和资源地址。
          </p>
        </div>
      </div>
    );
  }
  return (
    <TestPlanDetail
      agentVersions={assetsQuery.data.agentVersions}
      datasetVersions={assetsQuery.data.datasetVersions}
      environments={assetsQuery.data.environments}
      onCreateVersion={async (payload) => {
        await createTestPlanVersion(projectId, planId, payload);
        await versionsQuery.refetch();
      }}
      onPublish={async (versionId) => {
        await publishTestPlanVersion(projectId, planId, versionId);
        await versionsQuery.refetch();
      }}
      onUpdateVersion={async (versionId, payload) => {
        await updateTestPlanVersion(projectId, planId, versionId, payload);
        await versionsQuery.refetch();
      }}
      plan={planQuery.data}
      versions={versionsQuery.data}
    />
  );
}

async function loadAssetOptions(projectId: string): Promise<{
  agentVersions: VersionAssetOption[];
  datasetVersions: VersionAssetOption[];
  environments: VersionAssetOption[];
}> {
  const [agentPage, datasetPage, environments] = await Promise.all([
    listAgents(projectId),
    listDatasets(projectId),
    listEnvironmentTemplates(projectId),
  ]);
  const agentVersions = (
    await Promise.all(
      agentPage.items.map(async (agent) =>
        (await listAgentVersions(projectId, agent.id)).map((version) => ({
          id: version.id,
          label: `${agent.name} v${version.version_number}`,
          status: version.status,
        })),
      ),
    )
  ).flat();
  const datasetVersions = (
    await Promise.all(
      datasetPage.items.map(async (dataset) =>
        (await listDatasetVersions(projectId, dataset.id)).map((version) => ({
          id: version.id,
          label: `${dataset.name} v${version.version_number}`,
          status: version.status,
        })),
      ),
    )
  ).flat();
  return {
    agentVersions,
    datasetVersions,
    environments: environments.map((template) => ({
      id: template.id,
      label: template.name,
    })),
  };
}
