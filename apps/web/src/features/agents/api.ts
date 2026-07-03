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
import { CONTROL_API_URL } from "@/lib/api/base-url";
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
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/agents/${agentId}`,
    {
      method: "DELETE",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(problem?.detail ?? "删除 Agent 失败");
  }
  return;
}

async function agentMutation(
  projectId: string,
  agentId: string,
  suffix: string,
  method: string,
  body?: unknown,
) {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/agents/${agentId}${suffix}`,
    {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: body === undefined ? undefined : JSON.stringify(body),
    },
  );
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(problem?.detail ?? "Agent 操作失败");
  }
  return response.json();
}

export const updateAgent = (
  projectId: string,
  agentId: string,
  body: { name?: string; description?: string | null },
) => agentMutation(projectId, agentId, "", "PATCH", body);
export const setCurrentAgentVersion = (
  projectId: string,
  agentId: string,
  versionId: string,
) =>
  agentMutation(projectId, agentId, "/current-version", "PATCH", {
    version_id: versionId,
  });
export const setBaselineAgentVersion = (
  projectId: string,
  agentId: string,
  versionId: string,
) =>
  agentMutation(projectId, agentId, "/baseline-version", "PATCH", {
    version_id: versionId,
  });

export async function diffAgentVersions(
  projectId: string,
  agentId: string,
  v1: string,
  v2: string,
) {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/agents/${agentId}/versions/${v1}/diff/${v2}`,
    { credentials: "include" },
  );
  if (!response.ok) throw new Error("获取版本差异失败");
  return response.json();
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
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/agents/${agentId}/relationships`,
    { credentials: "include" },
  );
  if (!response.ok) throw new Error("加载 Agent 关联数据失败");
  return response.json();
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
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/agents/${agentId}/versions/${versionId}/validate-connection`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify({ input }),
    },
  );
  if (!response.ok) throw new Error("连接测试失败");
  return response.json() as Promise<{
    ok: boolean;
    status_code: number;
    latency_ms: number;
    response_preview: unknown;
  }>;
}
