import {
  keepPreviousData,
  queryOptions,
  type QueryClient,
} from "@tanstack/react-query";

import {
  getDataset,
  listDatasets,
  listDatasetVersions,
  listTestCases,
} from "./api";

export const datasetQueries = {
  all: ["datasets"] as const,
  list(projectId: string, page = 1, pageSize = 10) {
    return queryOptions({
      queryFn: ({ signal }) => listDatasets(projectId, signal, page, pageSize),
      queryKey: ["datasets", projectId, page, pageSize] as const,
      placeholderData: keepPreviousData,
    });
  },
  detail(projectId: string, datasetId: string) {
    return queryOptions({
      queryFn: ({ signal }) => getDataset(projectId, datasetId, signal),
      queryKey: ["datasets", projectId, datasetId] as const,
    });
  },
  versions(projectId: string, datasetId: string) {
    return queryOptions({
      queryFn: ({ signal }) =>
        listDatasetVersions(projectId, datasetId, signal),
      queryKey: ["datasets", projectId, datasetId, "versions"] as const,
    });
  },
  cases(projectId: string, datasetId: string, versionId: string) {
    return queryOptions({
      queryFn: ({ signal }) =>
        listTestCases(projectId, datasetId, versionId, signal),
      queryKey: [
        "datasets",
        projectId,
        datasetId,
        "versions",
        versionId,
        "cases",
      ] as const,
    });
  },
};

export function invalidateDatasetList(client: QueryClient, projectId: string) {
  return client.invalidateQueries({
    queryKey: ["datasets", projectId],
  });
}
