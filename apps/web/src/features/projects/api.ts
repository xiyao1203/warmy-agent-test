import {
  createProjectApiV1ProjectsPost,
  getProjectApiV1ProjectsProjectIdGet,
  listMembersApiV1ProjectsProjectIdMembersGet,
  listProjectsApiV1ProjectsGet,
  type CreateProjectRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function listProjects() {
  const { data } = await listProjectsApiV1ProjectsGet({
    client: apiClient,
    throwOnError: true,
  });
  return data.items;
}

export async function createProject(payload: CreateProjectRequest) {
  const { data } = await createProjectApiV1ProjectsPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
  return data;
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
