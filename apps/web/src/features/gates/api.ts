import {
  createGateApiV1ProjectsProjectIdGatesPost,
  deleteGateApiV1ProjectsProjectIdGatesGateIdDelete,
  evaluateGateApiV1ProjectsProjectIdGatesGateIdEvaluatePost,
  listGatesApiV1ProjectsProjectIdGatesGet,
  listRunsApiV1ProjectsProjectIdRunsGet,
  type CreateGateRequest,
  type EvaluateGateRequest,
  type GateSummaryResponse,
  type RunResponse,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export type GateItem = GateSummaryResponse;
export type GateResult = { passed: boolean; failures: string[] };
export type GateRun = Pick<RunResponse, "created_at" | "id" | "status">;

export async function listGates(projectId: string, signal?: AbortSignal) {
  const { data } = await listGatesApiV1ProjectsProjectIdGatesGet({
    client: apiClient,
    path: { project_id: projectId },
    signal,
    throwOnError: true,
  });
  return data.items;
}

export async function createGate(
  projectId: string,
  payload: CreateGateRequest,
) {
  const { data } = await createGateApiV1ProjectsProjectIdGatesPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data as GateItem;
}

export async function evaluateGate(
  projectId: string,
  gateId: string,
  payload: EvaluateGateRequest,
) {
  const { data } =
    await evaluateGateApiV1ProjectsProjectIdGatesGateIdEvaluatePost({
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: { gate_id: gateId, project_id: projectId },
      throwOnError: true,
    });
  return data as { gate_id: string; result: GateResult };
}

export async function listGateRuns(projectId: string, signal?: AbortSignal) {
  const { data } = await listRunsApiV1ProjectsProjectIdRunsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 50 },
    signal,
    throwOnError: true,
  });
  return data.items as GateRun[];
}

export async function deleteGate(projectId: string, gateId: string) {
  await deleteGateApiV1ProjectsProjectIdGatesGateIdDelete({
    client: apiClient,
    headers: csrfHeaders(),
    path: { gate_id: gateId, project_id: projectId },
    throwOnError: true,
  });
}
