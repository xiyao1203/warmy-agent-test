import {
  listReviewsApiV1ProjectsProjectIdReviewsGet,
  rejectReviewApiV1ProjectsProjectIdReviewsTaskIdRejectPost,
  scoreReviewApiV1ProjectsProjectIdReviewsTaskIdScorePost,
  skipReviewApiV1ProjectsProjectIdReviewsTaskIdSkipPost,
  type ReviewSummaryResponse,
  type ScoreReviewRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export type ReviewTask = ReviewSummaryResponse;

const reviewPath = (projectId: string, taskId: string) => ({
  project_id: projectId,
  task_id: taskId,
});

export async function listReviews(
  projectId: string,
  status?: string,
  signal?: AbortSignal,
) {
  const { data } = await listReviewsApiV1ProjectsProjectIdReviewsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100, status },
    signal,
    throwOnError: true,
  });
  return data.items;
}

export async function scoreReview(
  projectId: string,
  taskId: string,
  payload: ScoreReviewRequest,
) {
  const { data } =
    await scoreReviewApiV1ProjectsProjectIdReviewsTaskIdScorePost({
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: reviewPath(projectId, taskId),
      throwOnError: true,
    });
  return data as ReviewTask;
}

export async function rejectReview(
  projectId: string,
  taskId: string,
  opinion?: string,
) {
  const { data } =
    await rejectReviewApiV1ProjectsProjectIdReviewsTaskIdRejectPost({
      client: apiClient,
      headers: csrfHeaders(),
      path: reviewPath(projectId, taskId),
      query: { opinion },
      throwOnError: true,
    });
  return data as ReviewTask;
}

export async function skipReview(projectId: string, taskId: string) {
  const { data } = await skipReviewApiV1ProjectsProjectIdReviewsTaskIdSkipPost({
    client: apiClient,
    headers: csrfHeaders(),
    path: reviewPath(projectId, taskId),
    throwOnError: true,
  });
  return data as ReviewTask;
}
