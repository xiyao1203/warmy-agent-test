"use client";

import { useQuery } from "@tanstack/react-query";

import {
  deleteTestCase,
  getDataset,
  listDatasetVersions,
  listTestCases,
  importTestCases,
  previewTestCaseImport,
} from "./api";
import { DatasetDetail } from "./dataset-detail";

export function DatasetDetailScreen({
  datasetId,
  projectId,
}: {
  datasetId: string;
  projectId: string;
}) {
  const datasetQuery = useQuery({
    queryFn: () => getDataset(projectId, datasetId),
    queryKey: ["dataset", projectId, datasetId],
  });

  const versionsQuery = useQuery({
    queryFn: () => listDatasetVersions(projectId, datasetId),
    queryKey: ["dataset-versions", projectId, datasetId],
  });

  const latestVersion = versionsQuery.data?.[0];

  const casesQuery = useQuery({
    enabled: !!latestVersion,
    queryFn: () => listTestCases(projectId, datasetId, latestVersion!.id),
    queryKey: ["test-cases", projectId, datasetId, latestVersion?.id],
  });

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
          <h1 className="text-base font-semibold">数据集不存在或你无权访问</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            请返回数据集列表检查项目和资源地址。
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
      onDeleteCases={async (caseIds) => {
        if (!latestVersion) return;
        for (const cid of caseIds) {
          await deleteTestCase(projectId, datasetId, latestVersion.id, cid);
        }
        await refreshCases();
      }}
      onImport={async (content, format) => {
        if (!latestVersion) throw new Error("请先创建草稿版本");
        return importTestCases(projectId, datasetId, latestVersion.id, {
          content,
          format,
        });
      }}
      onPreviewImport={async (content, format) => {
        if (!latestVersion) throw new Error("请先创建草稿版本");
        return previewTestCaseImport(projectId, datasetId, latestVersion.id, {
          content,
          format,
        });
      }}
      onRefresh={refreshCases}
      projectId={projectId}
      versions={versionsQuery.data ?? []}
    />
  );
}
