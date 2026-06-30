import {
  createPlanApiV1ProjectsProjectIdTestPlansPost,
  createVersionApiV1ProjectsProjectIdTestPlansPlanIdVersionsPost,
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
import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export async function listTestPlans(projectId: string) {
  const { data } = await listPlansApiV1ProjectsProjectIdTestPlansGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    throwOnError: true,
  });
  return data;
}

export async function deleteTestPlan(projectId: string, planId: string) {
  const response = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/test-plans/${planId}`,
    {
      method: "DELETE",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!response.ok) throw await responseProblem(response, "删除测试计划失败");
}

export async function getTestPlan(projectId: string, planId: string) {
  const { data } = await getPlanApiV1ProjectsProjectIdTestPlansPlanIdGet({
    client: apiClient,
    path: { plan_id: planId, project_id: projectId },
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

export async function listTestPlanVersions(projectId: string, planId: string) {
  const { data } =
    await listVersionsApiV1ProjectsProjectIdTestPlansPlanIdVersionsGet({
      client: apiClient,
      path: { plan_id: planId, project_id: projectId },
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

export async function dryRunTestPlanVersion(
  projectId: string,
  planId: string,
  versionId: string,
) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/test-plans/${planId}/versions/${versionId}/dry-run`,
    {
      method: "POST",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!res.ok) throw await responseProblem(res, "测试计划试运行失败");
  return res.json();
}
