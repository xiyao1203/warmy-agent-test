import { listProjectsApiV1ProjectsGet } from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";

export async function listProjects() {
  const { data } = await listProjectsApiV1ProjectsGet({
    client: apiClient,
    throwOnError: true,
  });
  return data.items;
}
