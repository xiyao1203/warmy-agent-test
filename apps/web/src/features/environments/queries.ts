import { queryOptions, type QueryClient } from "@tanstack/react-query";

import { listEnvironmentTemplates } from "./api";

export const environmentQueries = {
  all: ["environments"] as const,
  list(projectId: string) {
    return queryOptions({
      queryFn: ({ signal }) => listEnvironmentTemplates(projectId, signal),
      queryKey: ["environments", projectId] as const,
    });
  },
};

export function invalidateEnvironmentList(
  client: QueryClient,
  projectId: string,
) {
  return client.invalidateQueries({
    queryKey: environmentQueries.list(projectId).queryKey,
  });
}
