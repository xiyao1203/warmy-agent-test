import {
  cancelRunApiV1ProjectsProjectIdRunsRunIdCancelPost,
  createRunApiV1ProjectsProjectIdRunsPost,
  getRunApiV1ProjectsProjectIdRunsRunIdGet,
  listCasesApiV1ProjectsProjectIdRunsRunIdCasesGet,
  listRunsApiV1ProjectsProjectIdRunsGet,
  listPlansApiV1ProjectsProjectIdTestPlansGet,
  listVersionsApiV1ProjectsProjectIdTestPlansPlanIdVersionsGet,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

const CONTROL_API_URL =
  process.env.NEXT_PUBLIC_CONTROL_API_URL ?? "http://localhost:8181";

export async function listRuns(projectId: string) {
  const { data } = await listRunsApiV1ProjectsProjectIdRunsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
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

export async function getRun(projectId: string, runId: string) {
  const { data } = await getRunApiV1ProjectsProjectIdRunsRunIdGet({
    client: apiClient,
    path: { project_id: projectId, run_id: runId },
    throwOnError: true,
  });
  return data;
}

export async function listRunCases(projectId: string, runId: string) {
  const { data } = await listCasesApiV1ProjectsProjectIdRunsRunIdCasesGet({
    client: apiClient,
    path: { project_id: projectId, run_id: runId },
    throwOnError: true,
  });
  return data.items;
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
): Promise<ArtifactItem[]> {
  const url = `${CONTROL_API_URL}/api/v1/projects/${projectId}/runs/${runId}/artifacts`;
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) return [];
  const data = await res.json();
  return (data as { items?: ArtifactItem[] }).items ?? [];
}

export function artifactDownloadUrl(
  projectId: string,
  artifactId: string,
): string {
  return `${CONTROL_API_URL}/api/v1/projects/${projectId}/artifacts/${artifactId}/download`;
}
