import {
  createExperimentApiV1ProjectsProjectIdExperimentsPost,
  getExperimentApiV1ProjectsProjectIdExperimentsExperimentIdGet,
  listExperimentsApiV1ProjectsProjectIdExperimentsGet,
  listRunsApiV1ProjectsProjectIdRunsGet,
  runExperimentApiV1ProjectsProjectIdExperimentsExperimentIdRunPost,
  type CreateExperimentRequest,
  type ExperimentSummaryResponse,
  type RunResponse,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export type ExperimentItem = ExperimentSummaryResponse;
export type ExperimentRun = Pick<
  RunResponse,
  "created_at" | "id" | "status" | "test_plan_version_id"
>;

export async function listExperimentRuns(
  projectId: string,
  signal?: AbortSignal,
) {
  const { data } = await listRunsApiV1ProjectsProjectIdRunsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    signal,
    throwOnError: true,
  });
  return data.items.filter((run) =>
    ["passed", "failed", "error"].includes(run.status),
  ) as ExperimentRun[];
}

export async function listExperiments(projectId: string, signal?: AbortSignal) {
  const { data } = await listExperimentsApiV1ProjectsProjectIdExperimentsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100, offset: 0 },
    signal,
    throwOnError: true,
  });
  return data.items;
}

export async function createExperiment(
  projectId: string,
  payload: CreateExperimentRequest,
) {
  const { data } = await createExperimentApiV1ProjectsProjectIdExperimentsPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data as ExperimentItem;
}

export async function getExperiment(projectId: string, experimentId: string) {
  const { data } =
    await getExperimentApiV1ProjectsProjectIdExperimentsExperimentIdGet({
      client: apiClient,
      path: { experiment_id: experimentId, project_id: projectId },
      throwOnError: true,
    });
  return data as ExperimentItem;
}

export async function runExperiment(projectId: string, experimentId: string) {
  const { data } =
    await runExperimentApiV1ProjectsProjectIdExperimentsExperimentIdRunPost({
      client: apiClient,
      headers: csrfHeaders(),
      path: { experiment_id: experimentId, project_id: projectId },
      throwOnError: true,
    });
  return data as ExperimentItem;
}
