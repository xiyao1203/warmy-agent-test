import {
  createPlanApiV1ProjectsProjectIdTestPlansPost,
  createVersionApiV1ProjectsProjectIdTestPlansPlanIdVersionsPost,
  deleteTestPlanApiV1ProjectsProjectIdTestPlansPlanIdDelete,
  dryRunApiV1ProjectsProjectIdTestPlansPlanIdVersionsVersionIdDryRunPost,
  getPlanApiV1ProjectsProjectIdTestPlansPlanIdGet,
  listPlansApiV1ProjectsProjectIdTestPlansGet,
  listTemplatesApiV1ProjectsProjectIdEnvironmentTemplatesGet,
  listVersionsApiV1ProjectsProjectIdTestPlansPlanIdVersionsGet,
  publishVersionApiV1ProjectsProjectIdTestPlansPlanIdVersionsVersionIdPublishPost,
  updateVersionApiV1ProjectsProjectIdTestPlansPlanIdVersionsVersionIdPatch,
  type CreateTestPlanRequest,
  type CreateTestPlanVersionRequest,
  type UpdateTestPlanVersionRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function listTestPlans(
  projectId: string,
  signal?: AbortSignal,
  page = 1,
  pageSize = 10,
) {
  const { data } = await listPlansApiV1ProjectsProjectIdTestPlansGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { page, page_size: pageSize },
    signal,
    throwOnError: true,
  });
  return data;
}

export async function deleteTestPlan(projectId: string, planId: string) {
  await deleteTestPlanApiV1ProjectsProjectIdTestPlansPlanIdDelete({
    client: apiClient,
    headers: csrfHeaders(),
    path: { plan_id: planId, project_id: projectId },
    throwOnError: true,
  });
}

export async function getTestPlan(
  projectId: string,
  planId: string,
  signal?: AbortSignal,
) {
  const { data } = await getPlanApiV1ProjectsProjectIdTestPlansPlanIdGet({
    client: apiClient,
    path: { plan_id: planId, project_id: projectId },
    signal,
    throwOnError: true,
  });
  return data;
}

export async function createTestPlan(
  projectId: string,
  payload: CreateTestPlanRequest,
) {
  const { data } = await createPlanApiV1ProjectsProjectIdTestPlansPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function listTestPlanVersions(
  projectId: string,
  planId: string,
  signal?: AbortSignal,
) {
  const { data } =
    await listVersionsApiV1ProjectsProjectIdTestPlansPlanIdVersionsGet({
      client: apiClient,
      path: { plan_id: planId, project_id: projectId },
      signal,
      throwOnError: true,
    });
  return data.items;
}

export async function createTestPlanVersion(
  projectId: string,
  planId: string,
  payload: CreateTestPlanVersionRequest,
) {
  const { data } =
    await createVersionApiV1ProjectsProjectIdTestPlansPlanIdVersionsPost({
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: { plan_id: planId, project_id: projectId },
      throwOnError: true,
    });
  return data;
}

export async function updateTestPlanVersion(
  projectId: string,
  planId: string,
  versionId: string,
  payload: UpdateTestPlanVersionRequest,
) {
  const { data } =
    await updateVersionApiV1ProjectsProjectIdTestPlansPlanIdVersionsVersionIdPatch(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          plan_id: planId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function publishTestPlanVersion(
  projectId: string,
  planId: string,
  versionId: string,
) {
  const { data } =
    await publishVersionApiV1ProjectsProjectIdTestPlansPlanIdVersionsVersionIdPublishPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          plan_id: planId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function listEnvironmentTemplates(
  projectId: string,
  signal?: AbortSignal,
) {
  const { data } =
    await listTemplatesApiV1ProjectsProjectIdEnvironmentTemplatesGet({
      client: apiClient,
      path: { project_id: projectId },
      query: { limit: 100 },
      signal,
      throwOnError: true,
    });
  return data.items;
}

export async function dryRunTestPlanVersion(
  projectId: string,
  planId: string,
  versionId: string,
) {
  const { data } =
    await dryRunApiV1ProjectsProjectIdTestPlansPlanIdVersionsVersionIdDryRunPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          plan_id: planId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data as Record<string, unknown>;
}
