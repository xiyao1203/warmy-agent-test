"use client";

import { useQuery } from "@tanstack/react-query";

import {
  createTestPlanVersion,
  publishTestPlanVersion,
  updateTestPlanVersion,
} from "./api";
import { TestPlanDetail } from "./test-plan-detail";
import { testPlanQueries } from "./queries";

export function TestPlanDetailScreen({
  planId,
  projectId,
}: {
  planId: string;
  projectId: string;
}) {
  const planQuery = useQuery(testPlanQueries.detail(projectId, planId));
  const versionsQuery = useQuery(testPlanQueries.versions(projectId, planId));
  const assetsQuery = useQuery(testPlanQueries.assets(projectId));
  if (planQuery.isPending || versionsQuery.isPending || assetsQuery.isPending) {
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
          <p className="mt-2 text-sm text-[var(--muted)]">
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
      gates={assetsQuery.data.gates}
      runs={assetsQuery.data.runs}
      scorers={assetsQuery.data.scorers}
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
