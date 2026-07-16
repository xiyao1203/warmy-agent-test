import {
  addCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesPost,
  createCaseTrialRunApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdTrialRunsPost,
  createDatasetApiV1ProjectsProjectIdDatasetsPost,
  createVersionApiV1ProjectsProjectIdDatasetsDatasetIdVersionsPost,
  deleteCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdDelete,
  exportCasesApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdExportGet,
  getDatasetApiV1ProjectsProjectIdDatasetsDatasetIdGet,
  importCasesApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdImportPost,
  listCasesApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesGet,
  listDatasetsApiV1ProjectsProjectIdDatasetsGet,
  listVersionsApiV1ProjectsProjectIdDatasetsDatasetIdVersionsGet,
  markCaseReadyApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdMarkReadyPost,
  publishVersionApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdPublishPost,
  previewImportApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdImportsPreviewPost,
  updateCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdPatch,
  validateCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdValidatePost,
  type CreateDatasetRequest,
  type CreateTestCaseRequest,
  type ImportTestCasesRequest,
  type UpdateTestCaseRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";

export async function listDatasets(projectId: string) {
  const { data } = await listDatasetsApiV1ProjectsProjectIdDatasetsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    throwOnError: true,
  });
  return data;
}

export async function deleteDataset(projectId: string, datasetId: string) {
  await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/datasets/${datasetId}`,
    {
      method: "DELETE",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
}

export async function getDataset(projectId: string, datasetId: string) {
  const { data } = await getDatasetApiV1ProjectsProjectIdDatasetsDatasetIdGet({
    client: apiClient,
    path: { dataset_id: datasetId, project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function createDataset(
  projectId: string,
  payload: CreateDatasetRequest,
) {
  const { data } = await createDatasetApiV1ProjectsProjectIdDatasetsPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function listDatasetVersions(
  projectId: string,
  datasetId: string,
) {
  const { data } =
    await listVersionsApiV1ProjectsProjectIdDatasetsDatasetIdVersionsGet({
      client: apiClient,
      path: { dataset_id: datasetId, project_id: projectId },
      throwOnError: true,
    });
  return data.items;
}

export async function createDatasetVersion(
  projectId: string,
  datasetId: string,
) {
  const { data } =
    await createVersionApiV1ProjectsProjectIdDatasetsDatasetIdVersionsPost({
      client: apiClient,
      headers: csrfHeaders(),
      path: { dataset_id: datasetId, project_id: projectId },
      throwOnError: true,
    });
  return data;
}

export async function listTestCases(
  projectId: string,
  datasetId: string,
  versionId: string,
) {
  const { data } =
    await listCasesApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesGet(
      {
        client: apiClient,
        path: {
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        query: { limit: 500 },
        throwOnError: true,
      },
    );
  return data.items;
}

export async function createTestCase(
  projectId: string,
  datasetId: string,
  versionId: string,
  payload: CreateTestCaseRequest,
) {
  const { data } =
    await addCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesPost(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function updateTestCase(
  projectId: string,
  datasetId: string,
  versionId: string,
  caseId: string,
  payload: UpdateTestCaseRequest,
) {
  const { data } =
    await updateCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdPatch(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          case_id: caseId,
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function deleteTestCase(
  projectId: string,
  datasetId: string,
  versionId: string,
  caseId: string,
) {
  await deleteCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdDelete(
    {
      client: apiClient,
      headers: csrfHeaders(),
      path: {
        case_id: caseId,
        dataset_id: datasetId,
        project_id: projectId,
        version_id: versionId,
      },
      throwOnError: true,
    },
  );
}

export async function validateTestCase(
  projectId: string,
  datasetId: string,
  versionId: string,
  caseId: string,
) {
  const { data } =
    await validateCaseApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdValidatePost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          case_id: caseId,
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function markTestCaseReady(
  projectId: string,
  datasetId: string,
  versionId: string,
  caseId: string,
) {
  const { data } =
    await markCaseReadyApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdMarkReadyPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          case_id: caseId,
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function createTestCaseTrialRun(
  projectId: string,
  datasetId: string,
  versionId: string,
  caseId: string,
  body: { agent_version_id: string; environment_template_id: string },
) {
  const { data } =
    await createCaseTrialRunApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdCasesCaseIdTrialRunsPost(
      {
        body,
        client: apiClient,
        headers: {
          ...csrfHeaders(),
          "Idempotency-Key":
            globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${caseId}`,
        },
        path: {
          case_id: caseId,
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function importTestCases(
  projectId: string,
  datasetId: string,
  versionId: string,
  payload: ImportTestCasesRequest,
) {
  const { data } =
    await importCasesApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdImportPost(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function previewTestCaseImport(
  projectId: string,
  datasetId: string,
  versionId: string,
  payload: ImportTestCasesRequest,
) {
  const { data } =
    await previewImportApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdImportsPreviewPost(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function exportTestCases(
  projectId: string,
  datasetId: string,
  versionId: string,
  format: "csv" | "json" | "jsonl",
) {
  const { data } =
    await exportCasesApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdExportGet(
      {
        client: apiClient,
        path: {
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        query: { format },
        throwOnError: true,
      },
    );
  return data;
}

export async function publishDatasetVersion(
  projectId: string,
  datasetId: string,
  versionId: string,
) {
  const { data } =
    await publishVersionApiV1ProjectsProjectIdDatasetsDatasetIdVersionsVersionIdPublishPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          dataset_id: datasetId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}
