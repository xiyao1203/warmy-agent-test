import {
  getScanApiV1ProjectsProjectIdSecurityScansScanIdGet,
  listAgentsApiV1ProjectsProjectIdAgentsGet,
  listScansApiV1ProjectsProjectIdSecurityScansGet,
  listVersionsApiV1ProjectsProjectIdAgentsAgentIdVersionsGet,
  triggerScanApiV1ProjectsProjectIdSecurityScansPost,
  type SecurityScanSummaryResponse,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export type Finding = {
  category: string;
  severity: string;
  title: string;
  description: string;
  vector: string;
  response: string;
  score: number;
};

export type SecurityScanItem = Omit<
  SecurityScanSummaryResponse,
  "findings" | "summary"
> & {
  findings: Finding[];
  summary: Record<string, number>;
};
export type SecurityTarget = { id: string; label: string };

export async function listScans(projectId: string, signal?: AbortSignal) {
  const { data } = await listScansApiV1ProjectsProjectIdSecurityScansGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 50 },
    signal,
    throwOnError: true,
  });
  return data.items as SecurityScanItem[];
}

export async function triggerScan(projectId: string, agentVersionId: string) {
  const { data } = await triggerScanApiV1ProjectsProjectIdSecurityScansPost({
    body: { agent_version_id: agentVersionId, scan_type: "full" },
    client: apiClient,
    headers: csrfHeaders(),
    path: { project_id: projectId },
    throwOnError: true,
  });
  return data as SecurityScanItem;
}

export async function listSecurityTargets(
  projectId: string,
  signal?: AbortSignal,
) {
  const { data: agents } = await listAgentsApiV1ProjectsProjectIdAgentsGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { limit: 100 },
    signal,
    throwOnError: true,
  });
  const targets = await Promise.all(
    agents.items.map(async (agent) => {
      const { data } =
        await listVersionsApiV1ProjectsProjectIdAgentsAgentIdVersionsGet({
          client: apiClient,
          path: { agent_id: agent.id, project_id: projectId },
          signal,
          throwOnError: true,
        });
      return data.items
        .filter((version) => version.status === "published")
        .map((version) => ({
          id: version.id,
          label: agent.name + " · v" + version.version_number,
        }));
    }),
  );
  return targets.flat();
}

export async function getScan(projectId: string, scanId: string) {
  const { data } = await getScanApiV1ProjectsProjectIdSecurityScansScanIdGet({
    client: apiClient,
    path: { project_id: projectId, scan_id: scanId },
    throwOnError: true,
  });
  return data as SecurityScanItem;
}
