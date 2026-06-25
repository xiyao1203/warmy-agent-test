import {
  createAgentApiV1ProjectsProjectIdAgentsPost,
  createVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsPost,
  getAgentApiV1ProjectsProjectIdAgentsAgentIdGet,
  listAgentsApiV1ProjectsProjectIdAgentsGet,
  listVersionsApiV1ProjectsProjectIdAgentsAgentIdVersionsGet,
  publishVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdPublishPost,
  updateVersionApiV1ProjectsProjectIdAgentsAgentIdVersionsVersionIdPatch,
  type CreateAgentRequest,
  type CreateAgentVersionRequest,
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
