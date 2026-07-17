import {
  cancelRunApiV1ProjectsProjectIdRunsRunIdCancelPost,
  createRunApiV1ProjectsProjectIdRunsPost,
  getRunApiV1ProjectsProjectIdRunsRunIdGet,
  getCalibrationApiV1ProjectsProjectIdRunsRunIdCalibrationGet,
  getJointGateApiV1ProjectsProjectIdRunsRunIdJointGateGet,
  getTrustLoopApiV1ProjectsProjectIdRunsRunIdTrustLoopGet,
  listCasesApiV1ProjectsProjectIdRunsRunIdCasesGet,
  listDiagnosticsApiV1ProjectsProjectIdRunsRunIdDiagnosticsGet,
  listArtifactsApiV1ProjectsProjectIdRunsRunIdArtifactsGet,
  listRegressionsApiV1ProjectsProjectIdRunsRunIdRegressionsGet,
  listRunsApiV1ProjectsProjectIdRunsGet,
  listPlansApiV1ProjectsProjectIdTestPlansGet,
  listVersionsApiV1ProjectsProjectIdTestPlansPlanIdVersionsGet,
} from "@warmy/generated-api-client";
import type {
  CalibrationResponse,
  DiagnosticResponse,
  JointGateDecisionResponse,
  RegressionCandidateResponse,
  TrustLoopResponse,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { CONTROL_API_URL } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export async function listRuns(projectId: string, signal?: AbortSignal) {
  const { data } = await listRunsApiV1ProjectsProjectIdRunsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    signal,
    throwOnError: true,
  });
  return data.items;
}

export async function createRun(projectId: string, testPlanVersionId: string) {
  const { data } = await createRunApiV1ProjectsProjectIdRunsPost({
    body: { test_plan_version_id: testPlanVersionId },
    client: apiClient,
    headers: {
      ...csrfHeaders(),
      "Idempotency-Key": crypto.randomUUID(),
    },
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function getRun(
  projectId: string,
  runId: string,
  signal?: AbortSignal,
) {
  const { data } = await getRunApiV1ProjectsProjectIdRunsRunIdGet({
    client: apiClient,
    path: { project_id: projectId, run_id: runId },
    signal,
    throwOnError: true,
  });
  return data;
}

export async function listRunCases(
  projectId: string,
  runId: string,
  signal?: AbortSignal,
) {
  const { data } = await listCasesApiV1ProjectsProjectIdRunsRunIdCasesGet({
    client: apiClient,
    path: { project_id: projectId, run_id: runId },
    signal,
    throwOnError: true,
  });
  return data.items;
}

export type RunTrustLoopData = {
  summary: TrustLoopResponse;
  diagnostics: DiagnosticResponse[];
  regressions: RegressionCandidateResponse[];
  calibration: CalibrationResponse;
  gate: JointGateDecisionResponse;
};

export async function getRunTrustLoop(
  projectId: string,
  runId: string,
): Promise<RunTrustLoopData> {
  const path = { project_id: projectId, run_id: runId };
  const [summary, diagnostics, regressions, calibration, gate] =
    await Promise.all([
      getTrustLoopApiV1ProjectsProjectIdRunsRunIdTrustLoopGet({
        client: apiClient,
        path,
        throwOnError: true,
      }),
      listDiagnosticsApiV1ProjectsProjectIdRunsRunIdDiagnosticsGet({
        client: apiClient,
        path,
        query: { limit: 100, offset: 0 },
        throwOnError: true,
      }),
      listRegressionsApiV1ProjectsProjectIdRunsRunIdRegressionsGet({
        client: apiClient,
        path,
        query: { limit: 100, offset: 0 },
        throwOnError: true,
      }),
      getCalibrationApiV1ProjectsProjectIdRunsRunIdCalibrationGet({
        client: apiClient,
        path,
        throwOnError: true,
      }),
      getJointGateApiV1ProjectsProjectIdRunsRunIdJointGateGet({
        client: apiClient,
        path,
        throwOnError: true,
      }),
    ]);
  return {
    calibration: calibration.data,
    diagnostics: diagnostics.data.items,
    gate: gate.data,
    regressions: regressions.data.items,
    summary: summary.data,
  };
}

export async function cancelRun(projectId: string, runId: string) {
  const { data } = await cancelRunApiV1ProjectsProjectIdRunsRunIdCancelPost({
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId, run_id: runId },
    throwOnError: true,
  });
  return data;
}

export function runEventsUrl(projectId: string, runId: string) {
  return new URL(
    `/api/v1/projects/${projectId}/runs/${runId}/events`,
    CONTROL_API_URL,
  ).toString();
}

export async function listPublishedPlanVersions(projectId: string) {
  const { data: plans } = await listPlansApiV1ProjectsProjectIdTestPlansGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    throwOnError: true,
  });
  const versions = await Promise.all(
    plans.items.map(async (plan) => {
      const { data } =
        await listVersionsApiV1ProjectsProjectIdTestPlansPlanIdVersionsGet({
          client: apiClient,
          path: { plan_id: plan.id, project_id: projectId },
          throwOnError: true,
        });
      return data.items
        .filter((version) => version.status === "published")
        .map((version) => ({
          id: version.id,
          label: `${plan.name} v${version.version_number}`,
        }));
    }),
  );
  return versions.flat();
}

// ── Artifact 产物 ────────────────────────────────────────────────────────

export interface ArtifactItem {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export async function listArtifacts(
  projectId: string,
  runId: string,
  signal?: AbortSignal,
): Promise<ArtifactItem[]> {
  const { data } =
    await listArtifactsApiV1ProjectsProjectIdRunsRunIdArtifactsGet({
      client: apiClient,
      path: { project_id: projectId, run_id: runId },
      signal,
      throwOnError: true,
    });
  return (data as { items?: ArtifactItem[] }).items ?? [];
}

export function artifactDownloadUrl(
  projectId: string,
  artifactId: string,
): string {
  return `${CONTROL_API_URL}/api/v1/projects/${projectId}/artifacts/${artifactId}/download`;
}

export async function uploadArtifact(
  projectId: string,
  runId: string,
  file: File,
): Promise<ArtifactItem> {
  const form = new FormData();
  form.append("file", file);
  const url = `${CONTROL_API_URL}/api/v1/projects/${projectId}/runs/${runId}/artifacts`;
  // raw-fetch-allowed: multipart upload stream is absent from the generated contract
  const res = await fetch(url, {
    body: form,
    credentials: "include",
    headers: { "X-Csrf-Token": csrfHeaders()["x-csrf-token"] || "" },
    method: "POST",
  });
  if (!res.ok) {
    throw await responseProblem(res, `上传失败 (${res.status})`);
  }
  return (await res.json()) as ArtifactItem;
}
