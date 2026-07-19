"use client";

import { useQuery } from "@tanstack/react-query";

import { agentQueries } from "@/features/agents";
import { environmentQueries } from "@/features/environments";

import {
  createDatasetVersion,
  createTestCaseTrialRun,
  createTestCase,
  deleteTestCase,
  importTestCases,
  markTestCaseReady,
  previewTestCaseImport,
  updateTestCase,
  validateTestCase,
} from "./api";
import { DatasetDetail } from "./dataset-detail";
import { datasetQueries } from "./queries";

export function DatasetDetailScreen({
  datasetId,
  projectId,
}: {
  datasetId: string;
  projectId: string;
}) {
  const datasetQuery = useQuery(datasetQueries.detail(projectId, datasetId));

  const versionsQuery = useQuery(datasetQueries.versions(projectId, datasetId));

  const latestVersion = versionsQuery.data?.[0];

  const casesQuery = useQuery({
    ...datasetQueries.cases(projectId, datasetId, latestVersion?.id ?? ""),
    enabled: !!latestVersion,
  });

  const agentsQuery = useQuery(agentQueries.list(projectId));

  const environmentsQuery = useQuery(environmentQueries.list(projectId));

  async function ensureEditableVersion() {
    if (latestVersion && latestVersion.status !== "published") {
      return latestVersion;
    }

    const refreshedVersions = await versionsQuery.refetch();
    const currentVersion = refreshedVersions.data?.[0];
    if (currentVersion && currentVersion.status !== "published") {
      return currentVersion;
    }

    if (currentVersion?.status === "published") {
      throw new Error("当前版本已发布，请先创建新的草稿版本");
    }

    const created = await createDatasetVersion(projectId, datasetId);
    await versionsQuery.refetch();
    return created;
  }

  if (datasetQuery.isPending || versionsQuery.isPending) {
    return (
      <DatasetDetail
        dataset={{
          id: datasetId,
          name: "加载中…",
          description: null,
          project_id: projectId,
          created_at: "",
          updated_at: "",
          created_by: "",
          updated_by: "",
        }}
        loading
        projectId={projectId}
      />
    );
  }

  if (datasetQuery.isError || versionsQuery.isError) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
        <div>
          <h1 className="text-base font-semibold">用例集不存在或你无权访问</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            请返回用例集列表检查项目和资源地址。
          </p>
        </div>
      </div>
    );
  }

  async function refreshCases() {
    await casesQuery.refetch();
  }

  return (
    <DatasetDetail
      cases={casesQuery.data ?? []}
      currentVersionId={latestVersion?.id}
      currentVersionPublished={latestVersion?.status === "published"}
      dataset={datasetQuery.data}
      onCreateCase={async (payload) => {
        const editableVersion = await ensureEditableVersion();
        await createTestCase(projectId, datasetId, editableVersion.id, payload);
        await versionsQuery.refetch();
      }}
      onDeleteCases={async (caseIds) => {
        if (!latestVersion) return;
        for (const cid of caseIds) {
          await deleteTestCase(projectId, datasetId, latestVersion.id, cid);
        }
        await refreshCases();
      }}
      onImport={async (content, format) => {
        const editableVersion = await ensureEditableVersion();
        const result = await importTestCases(
          projectId,
          datasetId,
          editableVersion.id,
          {
            content,
            format,
          },
        );
        await versionsQuery.refetch();
        return result;
      }}
      onPreviewImport={async (content, format) => {
        const editableVersion = await ensureEditableVersion();
        return previewTestCaseImport(projectId, datasetId, editableVersion.id, {
          content,
          format,
        });
      }}
      onRefresh={refreshCases}
      onUpdateCase={async (caseId, payload) => {
        if (!latestVersion) throw new Error("请先创建草稿版本");
        await updateTestCase(
          projectId,
          datasetId,
          latestVersion.id,
          caseId,
          payload,
        );
      }}
      onValidateCase={async (caseId) => {
        if (!latestVersion) throw new Error("请先创建草稿版本");
        return validateTestCase(projectId, datasetId, latestVersion.id, caseId);
      }}
      onMarkReady={async (caseId) => {
        if (!latestVersion) throw new Error("请先创建草稿版本");
        await markTestCaseReady(projectId, datasetId, latestVersion.id, caseId);
      }}
      onTrialRun={async (caseId, agentVersionId, environmentTemplateId) => {
        if (!latestVersion) throw new Error("请先创建草稿版本");
        return createTestCaseTrialRun(
          projectId,
          datasetId,
          latestVersion.id,
          caseId,
          {
            agent_version_id: agentVersionId,
            environment_template_id: environmentTemplateId,
          },
        );
      }}
      projectId={projectId}
      trialAgents={(agentsQuery.data?.items ?? []).flatMap((agent) =>
        agent.current_version_id
          ? [{ id: agent.current_version_id, name: agent.name }]
          : [],
      )}
      trialEnvironments={(environmentsQuery.data?.items ?? []).map((environment) => ({
        id: environment.id,
        name: environment.name,
      }))}
      versions={versionsQuery.data ?? []}
    />
  );
}
