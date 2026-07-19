import { queryOptions, type QueryClient } from "@tanstack/react-query";

import { listEnvironmentTemplatePage } from "./api";

export const environmentQueries = {
  all: ["environments"] as const,
  list(projectId: string, page = 1, pageSize = 10) {
    return queryOptions({
      queryFn: ({ signal }) =>
        listEnvironmentTemplatePage(projectId, signal, page, pageSize),
      queryKey: ["environments", projectId, page, pageSize] as const,
    });
  },
};

export function invalidateEnvironmentList(
  client: QueryClient,
  projectId: string,
) {
  return client.invalidateQueries({
    queryKey: ["environments", projectId],
  });
}
