import {
  createTemplateApiV1ProjectsProjectIdEnvironmentTemplatesPost,
  createCredentialApiV1ProjectsProjectIdCredentialsPost,
  createVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsPost,
  deleteTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdDelete,
  getTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdGet,
  getVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdGet,
  listTemplatesApiV1ProjectsProjectIdEnvironmentTemplatesGet,
  listCredentialsApiV1ProjectsProjectIdCredentialsGet,
  listVersionsApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsGet,
  publishVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdPublishPost,
  updateTemplateApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdPatch,
  updateVersionApiV1ProjectsProjectIdEnvironmentTemplatesTemplateIdVersionsVersionIdPatch,
  type CreateEnvironmentTemplateRequest,
  type CreateEnvironmentVersionRequest,
  type CreateCredentialBindingRequest,
  type UpdateEnvironmentTemplateRequest,
  type UpdateEnvironmentVersionRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

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
  const { data } = await listCredentialsApiV1ProjectsProjectIdCredentialsGet({
    client: apiClient,
    path: { project_id: projectId },
    throwOnError: true,
  });
  return (data as { items?: CredentialBinding[] }).items ?? [];
}

export async function createCredentialBinding(
  projectId: string,
  payload: CreateCredentialBindingRequest,
) {
  const { data } = await createCredentialApiV1ProjectsProjectIdCredentialsPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data as CredentialBinding;
}

export async function listEnvironmentTemplates(
  projectId: string,
  signal?: AbortSignal,
) {
  const data = await listEnvironmentTemplatePage(projectId, signal, 1, 50);
  return data.items;
}

export async function listEnvironmentTemplatePage(
  projectId: string,
  signal?: AbortSignal,
  page = 1,
  pageSize = 10,
) {
  const { data } =
    await listTemplatesApiV1ProjectsProjectIdEnvironmentTemplatesGet({
      client: apiClient,
      path: { project_id: projectId },
      query: { page, page_size: pageSize },
      signal,
      throwOnError: true,
    });
  return data;
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
