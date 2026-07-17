import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

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

export type SecurityTarget = {
  id: string;
  label: string;
};

export async function listScans(projectId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/security/scans?limit=50`,
    { credentials: "include" },
  );
  if (!res.ok) throw await responseProblem(res, "加载安全扫描失败");
  const data = await res.json();
  return data.items as SecurityScanItem[];
}

export async function triggerScan(projectId: string, agentVersionId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/security/scans`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify({
        agent_version_id: agentVersionId,
        scan_type: "full",
      }),
    },
  );
  if (!res.ok) throw await responseProblem(res, "安全扫描启动失败");
  return res.json() as Promise<SecurityScanItem>;
}

export async function listSecurityTargets(projectId: string) {
  const agentsResponse = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/agents?limit=100`,
    { credentials: "include" },
  );
  if (!agentsResponse.ok)
    throw await responseProblem(agentsResponse, "加载 Agent 失败");
  const agents = (await agentsResponse.json()).items as Array<{
    id: string;
    name: string;
  }>;
  const targets = await Promise.all(
    agents.map(async (agent) => {
      const response = await fetch(
        `${API_BASE}/api/v1/projects/${projectId}/agents/${agent.id}/versions`,
        { credentials: "include" },
      );
      if (!response.ok) return [];
      const versions = (await response.json()).items as Array<{
        id: string;
        version_number: number;
        status: string;
      }>;
      return versions
        .filter((version) => version.status === "published")
        .map((version) => ({
          id: version.id,
          label: `${agent.name} · v${version.version_number}`,
        }));
    }),
  );
  return targets.flat() as SecurityTarget[];
}

export async function getScan(projectId: string, scanId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/security/scans/${scanId}`,
    { credentials: "include" },
  );
  if (!res.ok) throw await responseProblem(res, "加载安全扫描详情失败");
  return res.json() as Promise<SecurityScanItem>;
}
import type { SecurityScanSummaryResponse } from "@warmy/generated-api-client";
