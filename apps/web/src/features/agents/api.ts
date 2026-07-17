import {
  createAgentApiV1ProjectsProjectIdAgentsPost,
  createVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsPost,
  deleteAgentApiV1ProjectsProjectIdAgentsAgentIdDelete,
  diffVersionsApiV1ProjectsProjectIdAgentsAgentIdVersionsV1IdDiffV2IdGet,
  getAgentApiV1ProjectsProjectIdAgentsAgentIdGet,
  getRelationshipsApiV1ProjectsProjectIdAgentsAgentIdRelationshipsGet,
  listAgentsApiV1ProjectsProjectIdAgentsGet,
  listVersionsApiV1ProjectsProjectIdAgentsAgentIdVersionsGet,
  publishVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdPublishPost,
  updateAgentApiV1ProjectsProjectIdAgentsAgentIdPatch,
  updateVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdPatch,
  validateConnectionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdValidateConnectionPost,
  type CreateAgentRequest,
  type CreateAgentVersionRequest,
  type UpdateAgentRequest,
  type UpdateAgentVersionRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function listAgents(projectId: string) {
  const { data } = await listAgentsApiV1ProjectsProjectIdAgentsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    throwOnError: true,
  });
  return data;
}

export async function getAgent(projectId: string, agentId: string) {
  const { data } = await getAgentApiV1ProjectsProjectIdAgentsAgentIdGet({
    client: apiClient,
    path: { agent_id: agentId, project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function createAgent(
  projectId: string,
  payload: CreateAgentRequest,
) {
  const { data } = await createAgentApiV1ProjectsProjectIdAgentsPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function deleteAgent(projectId: string, agentId: string) {
  await deleteAgentApiV1ProjectsProjectIdAgentsAgentIdDelete({
    client: apiClient,
    headers: csrfHeaders(),
    path: { agent_id: agentId, project_id: projectId },
    throwOnError: true,
  });
}

export async function updateAgent(
  projectId: string,
  agentId: string,
  body: UpdateAgentRequest,
) {
  const { data } = await updateAgentApiV1ProjectsProjectIdAgentsAgentIdPatch({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    path: { agent_id: agentId, project_id: projectId },
    throwOnError: true,
  });
  return data;
}

export async function setCurrentAgentVersion(
  projectId: string,
  agentId: string,
  versionId: string,
) {
  const { data } = await apiClient.patch({
    body: { version_id: versionId },
    headers: csrfHeaders(),
    path: { agent_id: agentId, project_id: projectId },
    throwOnError: true,
    url: "/api/v1/projects/{project_id}/agents/{agent_id}/current-version",
  });
  return data;
}

export async function setBaselineAgentVersion(
  projectId: string,
  agentId: string,
  versionId: string,
) {
  const { data } = await apiClient.patch({
    body: { version_id: versionId },
    headers: csrfHeaders(),
    path: { agent_id: agentId, project_id: projectId },
    throwOnError: true,
    url: "/api/v1/projects/{project_id}/agents/{agent_id}/baseline-version",
  });
  return data;
}

export async function diffAgentVersions(
  projectId: string,
  agentId: string,
  v1: string,
  v2: string,
) {
  const { data } =
    await diffVersionsApiV1ProjectsProjectIdAgentsAgentIdVersionsV1IdDiffV2IdGet(
      {
        client: apiClient,
        path: {
          agent_id: agentId,
          project_id: projectId,
          v1_id: v1,
          v2_id: v2,
        },
        throwOnError: true,
      },
    );
  return data;
}

export type AgentRelationships = {
  plans: Array<{
    id: string;
    plan_id: string;
    name: string;
    version_number: number;
    status: string;
  }>;
  runs: Array<{
    id: string;
    status: string;
    agent_version_id: string;
    passed_cases: number;
    total_cases: number;
    created_at: string;
  }>;
  artifacts: Array<{
    id: string;
    run_id: string;
    filename: string;
    content_type: string;
    created_at: string;
  }>;
  experiments: Array<{ id: string; name: string; status: string }>;
  security_scans: Array<{
    id: string;
    status: string;
    scan_type: string;
    agent_version_id: string;
  }>;
  gates: Array<{
    id: string;
    gate_id: string;
    name: string;
    status: string;
    run_id: string;
  }>;
};

export async function getAgentRelationships(
  projectId: string,
  agentId: string,
): Promise<AgentRelationships> {
  const { data } =
    await getRelationshipsApiV1ProjectsProjectIdAgentsAgentIdRelationshipsGet({
      client: apiClient,
      path: { agent_id: agentId, project_id: projectId },
      throwOnError: true,
    });
  return data as AgentRelationships;
}

export async function listAgentVersions(projectId: string, agentId: string) {
  const { data } =
    await listVersionsApiV1ProjectsProjectIdAgentsAgentIdVersionsGet({
      client: apiClient,
      path: { agent_id: agentId, project_id: projectId },
      throwOnError: true,
    });
  return data.items;
}

export async function createAgentVersion(
  projectId: string,
  agentId: string,
  payload: CreateAgentVersionRequest,
) {
  const { data } =
    await createVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsPost({
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: { agent_id: agentId, project_id: projectId },
      throwOnError: true,
    });
  return data;
}

export async function updateAgentVersion(
  projectId: string,
  agentId: string,
  versionId: string,
  payload: UpdateAgentVersionRequest,
) {
  const { data } =
    await updateVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdPatch(
      {
        body: payload,
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          agent_id: agentId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function publishAgentVersion(
  projectId: string,
  agentId: string,
  versionId: string,
) {
  const { data } =
    await publishVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdPublishPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          agent_id: agentId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data;
}

export async function validateAgentConnection(
  projectId: string,
  agentId: string,
  versionId: string,
  input: Record<string, unknown>,
) {
  const { data } =
    await validateConnectionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdValidateConnectionPost(
      {
        body: { input },
        client: apiClient,
        headers: csrfHeaders(),
        path: {
          agent_id: agentId,
          project_id: projectId,
          version_id: versionId,
        },
        throwOnError: true,
      },
    );
  return data as {
    ok: boolean;
    status_code: number;
    latency_ms: number;
    response_preview: unknown;
  };
}
