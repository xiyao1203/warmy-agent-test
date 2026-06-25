"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  createDatasetVersion,
  createTestCase,
  deleteTestCase,
  exportTestCases,
  getDataset,
  importTestCases,
  listDatasetVersions,
  listTestCases,
  publishDatasetVersion,
  updateTestCase,
} from "./api";
import { DatasetDetail } from "./dataset-detail";

export function DatasetDetailScreen({
  datasetId,
  projectId,
}: {
  datasetId: string;
  projectId: string;
}) {
  const [selectedVersionId, setSelectedVersionId] = useState<string>();
  const datasetQuery = useQuery({
    queryFn: () => getDataset(projectId, datasetId),
    queryKey: ["dataset", projectId, datasetId],
  });
  const versionsQuery = useQuery({
    queryFn: () => listDatasetVersions(projectId, datasetId),
    queryKey: ["dataset-versions", projectId, datasetId],
  });
  const activeVersionId = selectedVersionId ?? versionsQuery.data?.[0]?.id;
  const casesQuery = useQuery({
    enabled: Boolean(activeVersionId),
    queryFn: () =>
      listTestCases(projectId, datasetId, activeVersionId as string),
    queryKey: ["test-cases", projectId, datasetId, activeVersionId],
  });

  if (
    datasetQuery.isPending ||
    versionsQuery.isPending ||
    (activeVersionId && casesQuery.isPending)
  ) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        正在加载数据集详情…
      </div>
    );
  }
  if (datasetQuery.isError || versionsQuery.isError || casesQuery.isError) {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center px-6 text-center">
        <div>
          <h1 className="text-base font-semibold">数据集不存在或你无权访问</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            请返回数据集列表检查项目和资源地址。
          </p>
        </div>
      </div>
    );
  }

  async function refreshVersions() {
    const result = await versionsQuery.refetch();
    if (!activeVersionId && result.data?.length) {
      setSelectedVersionId(result.data[0].id);
    }
  }

  async function refreshCases() {
    if (activeVersionId) await casesQuery.refetch();
  }

  return (
    <DatasetDetail
      cases={casesQuery.data ?? []}
      dataset={datasetQuery.data}
      onCreateCase={async (versionId, payload) => {
        await createTestCase(projectId, datasetId, versionId, payload);
        await refreshCases();
      }}
      onCreateVersion={async () => {
        const version = await createDatasetVersion(projectId, datasetId);
        setSelectedVersionId(version.id);
        await refreshVersions();
      }}
      onDeleteCase={async (versionId, caseId) => {
        await deleteTestCase(projectId, datasetId, versionId, caseId);
        await refreshCases();
      }}
      onExport={(versionId, format) =>
        exportTestCases(projectId, datasetId, versionId, format)
      }
      onImport={async (versionId, payload) => {
        await importTestCases(projectId, datasetId, versionId, payload);
        await refreshCases();
      }}
      onPublish={async (versionId) => {
        await publishDatasetVersion(projectId, datasetId, versionId);
        await refreshVersions();
      }}
      onSelectVersion={setSelectedVersionId}
      onUpdateCase={async (versionId, caseId, payload) => {
        await updateTestCase(
          projectId,
          datasetId,
          versionId,
          caseId,
          payload,
        );
        await refreshCases();
      }}
      selectedVersionId={activeVersionId}
      versions={versionsQuery.data}
    />
  );
}
