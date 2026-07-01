import {
  createTemplateApiV1ProjectsProjectIdEnvironmentTemplatesPost,
  createVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsPost,
  deleteTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdDelete,
  getTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdGet,
  getVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdGet,
  listTemplatesApiV1ProjectsProjectIdEnvironmentTemplatesGet,
  listVersionsApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsGet,
  publishVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdPublishPost,
  updateTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdPatch,
  updateVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdPatch,
  type CreateEnvironmentTemplateRequest,
  type CreateEnvironmentVersionRequest,
  type UpdateEnvironmentTemplateRequest,
  type UpdateEnvironmentVersionRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { CONTROL_API_URL } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export type CredentialBinding = {
  id: string;
  alias: string;
  kind: string;
  injection_location: string;
  injection_name: string;
  masked_hint: string;
  updated_at: string;
};

export async function listCredentialBindings(projectId: string) {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/credentials`,
    { credentials: "include" },
  );
  if (!response.ok) throw await responseProblem(response, "加载凭证失败");
  return ((await response.json()).items ?? []) as CredentialBinding[];
}

export async function createCredentialBinding(
  projectId: string,
  payload: {
    alias: string;
    kind: string;
    injection_location: string;
    injection_name: string;
    value: string;
  },
) {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/credentials`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) throw await responseProblem(response, "保存凭证失败");
  return response.json() as Promise<CredentialBinding>;
}

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

// ── Environment version APIs ─────────────────────────────────────────────

export async function listEnvironmentVersions(
  projectId: string,
  templateId: string,
) {
  const { data } =
    await listVersionsApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsGet(
      {
        client: apiClient,
        path: { project_id: projectId, template_id: templateId },
        throwOnError: true,
      },
    );
  return data.items;
}

export async function getEnvironmentVersion(
  projectId: string,
  templateId: string,
  versionId: string,
) {
  const { data } =
    await getVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdGet(
      {
        client: apiClient,
        path: {
          project_id: projectId,
          template_id: templateId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function createEnvironmentVersion(
  projectId: string,
  templateId: string,
  payload: CreateEnvironmentVersionRequest,
) {
  const { data } =
    await createVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsPost(
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

export async function updateEnvironmentVersion(
  projectId: string,
  templateId: string,
  versionId: string,
  payload: UpdateEnvironmentVersionRequest,
) {
  const { data } =
    await updateVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdPatch(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          project_id: projectId,
          template_id: templateId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function publishEnvironmentVersion(
  projectId: string,
  templateId: string,
  versionId: string,
) {
  const { data } =
    await publishVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdPublishPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          project_id: projectId,
          template_id: templateId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}
