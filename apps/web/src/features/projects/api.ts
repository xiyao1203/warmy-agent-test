import {
  archiveProjectApiV1ProjectsProjectIdArchivePost,
  createProjectApiV1ProjectsPost,
  getProjectApiV1ProjectsProjectIdGet,
  listMembersApiV1ProjectsProjectIdMembersGet,
  listProjectsApiV1ProjectsGet,
  renameProjectApiV1ProjectsProjectIdPatch,
  type CreateProjectRequest,
  type RenameProjectRequest,
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

export async function listProjectPage(page = 1, pageSize = 10) {
  const { data } = await listProjectsApiV1ProjectsGet({
    client: apiClient,
    query: { page, page_size: pageSize },
    throwOnError: true,
  });
  return data;
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

export async function renameProject(
  projectId: string,
  payload: RenameProjectRequest,
) {
  const { data } = await renameProjectApiV1ProjectsProjectIdPatch({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function archiveProject(projectId: string) {
  const { data } = await archiveProjectApiV1ProjectsProjectIdArchivePost({
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
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
