"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { problemKind } from "@/lib/api/problem";
import { usePaginationState } from "@/lib/use-pagination-state";

import { createDataset, deleteDataset } from "./api";
import { DatasetList } from "./dataset-list";
import { datasetQueries, invalidateDatasetList } from "./queries";

export function DatasetListScreen({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const pagination = usePaginationState();
  const datasetsQuery = useQuery(
    datasetQueries.list(projectId, pagination.page, pagination.pageSize),
  );

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
      onPageChange={pagination.setPage}
      onPageSizeChange={pagination.setPageSize}
      page={datasetsQuery.data.page ?? pagination.page}
      pageSize={pagination.pageSize}
      projectId={projectId}
      total={datasetsQuery.data.total}
      totalPages={datasetsQuery.data.total_pages}
    />
  );
}
