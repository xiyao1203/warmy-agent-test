import {
  createScorerApiV1ProjectsProjectIdScorersPost,
  deleteScorerApiV1ProjectsProjectIdScorersScorerIdDelete,
  listScorersApiV1ProjectsProjectIdScorersGet,
  trialScorerApiV1ProjectsProjectIdScorersScorerIdTrialPost,
  updateScorerApiV1ProjectsProjectIdScorersScorerIdPatch,
  type CreateScorerRequest,
  type ScorerSummaryResponse,
  type TrialScorerRequest,
  type UpdateScorerRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export type ScorerItem = ScorerSummaryResponse;

const scorerPath = (projectId: string, scorerId: string) => ({
  project_id: projectId,
  scorer_id: scorerId,
});

export async function listScorers(projectId: string, signal?: AbortSignal) {
  const { data } = await listScorersApiV1ProjectsProjectIdScorersGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    signal,
    throwOnError: true,
  });
  return data.items;
}

export async function listScorerPage(
  projectId: string,
  signal?: AbortSignal,
  page = 1,
  pageSize = 10,
) {
  const { data } = await listScorersApiV1ProjectsProjectIdScorersGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { page, page_size: pageSize },
    signal,
    throwOnError: true,
  });
  return data;
}

export async function createScorer(
  projectId: string,
  payload: CreateScorerRequest,
) {
  const { data } = await createScorerApiV1ProjectsProjectIdScorersPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data as ScorerItem;
}

export async function updateScorer(
  projectId: string,
  scorerId: string,
  payload: UpdateScorerRequest,
) {
  const { data } = await updateScorerApiV1ProjectsProjectIdScorersScorerIdPatch(
    {
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: scorerPath(projectId, scorerId),
      throwOnError: true,
    },
  );
  return data as ScorerItem;
}

export async function deleteScorer(projectId: string, scorerId: string) {
  await deleteScorerApiV1ProjectsProjectIdScorersScorerIdDelete({
    client: apiClient,
    headers: csrfHeaders(),
    path: scorerPath(projectId, scorerId),
    throwOnError: true,
  });
}

export async function trialScorer(
  projectId: string,
  scorerId: string,
  payload: TrialScorerRequest,
) {
  const { data } =
    await trialScorerApiV1ProjectsProjectIdScorersScorerIdTrialPost({
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: scorerPath(projectId, scorerId),
      throwOnError: true,
    });
  return data as {
    score: number;
    passed: boolean;
    explanation: string;
    confidence: number;
  };
}
