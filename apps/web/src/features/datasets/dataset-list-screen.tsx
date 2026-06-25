"use client";

import { useQuery } from "@tanstack/react-query";

import { problemKind } from "@/lib/api/problem";

import { createDataset, listDatasets } from "./api";
import { DatasetList } from "./dataset-list";

export function DatasetListScreen({ projectId }: { projectId: string }) {
  const datasetsQuery = useQuery({
    queryFn: () => listDatasets(projectId),
    queryKey: ["datasets", projectId],
  });

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
        await datasetsQuery.refetch();
      }}
      projectId={projectId}
    />
  );
}
