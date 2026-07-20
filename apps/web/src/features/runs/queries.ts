import { queryOptions, type QueryClient } from "@tanstack/react-query";

import {
  getRun,
  getRunTrustLoop,
  listArtifacts,
  listPublishedPlanVersions,
  listRunCases,
  listRuns,
} from "./api";

export const runQueries = {
  all: ["runs"] as const,
  list(projectId: string, page = 1, pageSize = 10) {
    return queryOptions({
      queryFn: ({ signal }) => listRuns(projectId, signal, page, pageSize),
      queryKey: ["runs", projectId, page, pageSize] as const,
      refetchInterval: 5000,
    });
  },
  publishedPlanVersions(projectId: string) {
    return queryOptions({
      queryFn: () => listPublishedPlanVersions(projectId),
      queryKey: ["runs", projectId, "published-plan-versions"] as const,
    });
  },
  detail(projectId: string, runId: string) {
    return queryOptions({
      queryFn: ({ signal }) => getRun(projectId, runId, signal),
      queryKey: ["runs", projectId, runId] as const,
    });
  },
  cases(projectId: string, runId: string) {
    return queryOptions({
      queryFn: ({ signal }) => listRunCases(projectId, runId, signal),
      queryKey: ["runs", projectId, runId, "cases"] as const,
    });
  },
  artifacts(projectId: string, runId: string) {
    return queryOptions({
      queryFn: ({ signal }) => listArtifacts(projectId, runId, signal),
      queryKey: ["runs", projectId, runId, "artifacts"] as const,
    });
  },
  trustLoop(projectId: string, runId: string) {
    return queryOptions({
      queryFn: () => getRunTrustLoop(projectId, runId),
      queryKey: ["runs", projectId, runId, "trust-loop"] as const,
    });
  },
};

export function invalidateRunList(client: QueryClient, projectId: string) {
  return client.invalidateQueries({
    queryKey: ["runs", projectId],
  });
}
