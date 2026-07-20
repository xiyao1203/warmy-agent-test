import {
  keepPreviousData,
  queryOptions,
  type QueryClient,
} from "@tanstack/react-query";

import { getTestPlan, listTestPlans, listTestPlanVersions } from "./api";
import { loadTestPlanAssetOptions } from "./asset-options";

export const testPlanQueries = {
  all: ["test-plans"] as const,
  list(projectId: string, page = 1, pageSize = 10) {
    return queryOptions({
      queryFn: ({ signal }) => listTestPlans(projectId, signal, page, pageSize),
      queryKey: ["test-plans", projectId, page, pageSize] as const,
      placeholderData: keepPreviousData,
    });
  },
  detail(projectId: string, planId: string) {
    return queryOptions({
      queryFn: ({ signal }) => getTestPlan(projectId, planId, signal),
      queryKey: ["test-plans", projectId, planId] as const,
    });
  },
  versions(projectId: string, planId: string) {
    return queryOptions({
      queryFn: ({ signal }) => listTestPlanVersions(projectId, planId, signal),
      queryKey: ["test-plans", projectId, planId, "versions"] as const,
    });
  },
  assets(projectId: string) {
    return queryOptions({
      queryFn: ({ signal }) => loadTestPlanAssetOptions(projectId, signal),
      queryKey: ["test-plans", projectId, "assets"] as const,
    });
  },
};

export function invalidateTestPlanList(client: QueryClient, projectId: string) {
  return client.invalidateQueries({
    queryKey: ["test-plans", projectId],
  });
}
