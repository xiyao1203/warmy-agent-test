import { queryOptions, type QueryClient } from "@tanstack/react-query";

import { listBrowserProfilePage } from "./api";

export const browserProfileQueries = {
  all: ["browser-profiles"] as const,
  list(projectId: string, page = 1, pageSize = 10) {
    return queryOptions({
      queryFn: ({ signal }) =>
        listBrowserProfilePage(projectId, signal, page, pageSize),
      queryKey: ["browser-profiles", projectId, page, pageSize] as const,
    });
  },
};

export function invalidateBrowserProfileList(
  client: QueryClient,
  projectId: string,
) {
  return client.invalidateQueries({
    queryKey: ["browser-profiles", projectId],
  });
}
