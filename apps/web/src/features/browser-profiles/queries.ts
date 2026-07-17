import { queryOptions, type QueryClient } from "@tanstack/react-query";

import { listBrowserProfiles } from "./api";

export const browserProfileQueries = {
  all: ["browser-profiles"] as const,
  list(projectId: string) {
    return queryOptions({
      queryFn: ({ signal }) => listBrowserProfiles(projectId, signal),
      queryKey: ["browser-profiles", projectId] as const,
    });
  },
};

export function invalidateBrowserProfileList(
  client: QueryClient,
  projectId: string,
) {
  return client.invalidateQueries({
    queryKey: browserProfileQueries.list(projectId).queryKey,
  });
}
