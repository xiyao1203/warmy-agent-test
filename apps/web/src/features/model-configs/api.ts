import {
  createConfigApiV1ProjectsProjectIdModelConfigsPost,
  deleteConfigApiV1ProjectsProjectIdModelConfigsModelConfigIdDelete,
  listConfigsApiV1ProjectsProjectIdModelConfigsGet,
  listDefaultsApiV1ProjectsProjectIdModelDefaultsGet,
  setDefaultApiV1ProjectsProjectIdModelDefaultsPurposePut,
  testConnectionApiV1ProjectsProjectIdModelConfigsModelConfigIdTestConnectionPost,
  updateConfigApiV1ProjectsProjectIdModelConfigsModelConfigIdPatch,
  type CreateModelConfigRequest,
  type ModelPurpose,
  type UpdateModelConfigRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function listModelConfigs(projectId: string) {
  const { data } = await listConfigsApiV1ProjectsProjectIdModelConfigsGet({
    client: apiClient,
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data.items;
}

export async function listModelDefaults(projectId: string) {
  const { data } = await listDefaultsApiV1ProjectsProjectIdModelDefaultsGet({
    client: apiClient,
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data.items;
}

export async function createModelConfig(
  projectId: string,
  body: CreateModelConfigRequest,
) {
  await createConfigApiV1ProjectsProjectIdModelConfigsPost({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
}

export async function updateModelConfig(
  projectId: string,
  modelConfigId: string,
  body: UpdateModelConfigRequest,
) {
  await updateConfigApiV1ProjectsProjectIdModelConfigsModelConfigIdPatch({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId, model_config_id: modelConfigId },
    throwOnError: true,
  });
}

export async function deleteModelConfig(
  projectId: string,
  modelConfigId: string,
) {
  await deleteConfigApiV1ProjectsProjectIdModelConfigsModelConfigIdDelete({
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId, model_config_id: modelConfigId },
    throwOnError: true,
  });
}

export async function setModelDefault(
  projectId: string,
  purpose: ModelPurpose,
  modelConfigId: string,
) {
  await setDefaultApiV1ProjectsProjectIdModelDefaultsPurposePut({
    body: { model_config_id: modelConfigId },
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId, purpose },
    throwOnError: true,
  });
}

export async function testModelConnection(
  projectId: string,
  modelConfigId: string,
) {
  const { data } =
    await testConnectionApiV1ProjectsProjectIdModelConfigsModelConfigIdTestConnectionPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: { project_id: projectId, model_config_id: modelConfigId },
        throwOnError: true,
      },
    );
  return data as { ok: boolean; latency_ms: number; total_tokens: number };
}
