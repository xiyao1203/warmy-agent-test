import {
  createTemplateApiV1ProjectsProjectIdEnvironmentTemplatesPost,
  deleteTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdDelete,
  getTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdGet,
  listTemplatesApiV1ProjectsProjectIdEnvironmentTemplatesGet,
  updateTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdPatch,
  type CreateEnvironmentTemplateRequest,
  type UpdateEnvironmentTemplateRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function listEnvironmentTemplates(projectId: string) {
  const { data } =
    await listTemplatesApiV1ProjectsProjectIdEnvironmentTemplatesGet({
      client: apiClient,
      path: { project_id: projectId },
      query: { limit: 100 },
      throwOnError: true,
    });
  return data.items;
}

export async function getEnvironmentTemplate(
  projectId: string,
  templateId: string,
) {
  const { data } =
    await getTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdGet({
      client: apiClient,
      path: { project_id: projectId, template_id: templateId },
      throwOnError: true,
    });
  return data;
}

export async function createEnvironmentTemplate(
  projectId: string,
  payload: CreateEnvironmentTemplateRequest,
) {
  const { data } =
    await createTemplateApiV1ProjectsProjectIdEnvironmentTemplatesPost({
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: { project_id: projectId },
      throwOnError: true,
    });
  return data;
}

export async function updateEnvironmentTemplate(
  projectId: string,
  templateId: string,
  payload: UpdateEnvironmentTemplateRequest,
) {
  const { data } =
    await updateTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdPatch(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: { project_id: projectId, template_id: templateId },
        throwOnError: true,
      },
    );
  return data;
}

export async function deleteEnvironmentTemplate(
  projectId: string,
  templateId: string,
) {
  await deleteTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdDelete(
    {
      client: apiClient,
      headers: csrfHeaders(),
      path: { project_id: projectId, template_id: templateId },
      throwOnError: true,
    },
  );
}
