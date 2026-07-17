"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { problemKind } from "@/lib/api/problem";

import { createDataset, deleteDataset } from "./api";
import { DatasetList } from "./dataset-list";
import { datasetQueries, invalidateDatasetList } from "./queries";

export function DatasetListScreen({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const datasetsQuery = useQuery(datasetQueries.list(projectId));

  if (datasetsQuery.isPending) {
    return <DatasetList loading projectId={projectId} />;
  }
  if (datasetsQuery.isError) {
    const kind = problemKind(datasetsQuery.error);
    return (
      <DatasetList
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
    <DatasetList
      datasets={datasetsQuery.data.items}
      onCreate={async (payload) => {
        await createDataset(projectId, payload);
        await invalidateDatasetList(queryClient, projectId);
      }}
      onDelete={async (datasetId) => {
        await deleteDataset(projectId, datasetId);
        await invalidateDatasetList(queryClient, projectId);
      }}
      projectId={projectId}
    />
  );
}
