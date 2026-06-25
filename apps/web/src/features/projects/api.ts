import {
  getProjectApiV1ProjectsProjectIdGet,
  listMembersApiV1ProjectsProjectIdMembersGet,
  listProjectsApiV1ProjectsGet,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";

export async function listProjects() {
  const { data } = await listProjectsApiV1ProjectsGet({
    client: apiClient,
    throwOnError: true,
  });
  return data.items;
}

export async function getProject(projectId: string) {
  const { data } = await getProjectApiV1ProjectsProjectIdGet({
    client: apiClient,
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function listProjectMembers(projectId: string) {
  const { data } = await listMembersApiV1ProjectsProjectIdMembersGet({
    client: apiClient,
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data.items;
}
