import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
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

export type SecurityScanItem = {
  id: string;
  project_id: string;
  status: string;
  scan_type: string;
  findings: Finding[];
  summary: Record<string, number>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

export async function listScans(projectId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/security/scans?limit=50`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error("Failed to list scans");
  const data = await res.json();
  return data.items as SecurityScanItem[];
}

export async function triggerScan(projectId: string, agentEndpoint: string) {
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
        agent_endpoint: agentEndpoint,
        scan_type: "full",
      }),
    },
  );
  if (!res.ok) throw new Error("Failed to trigger scan");
  return res.json() as Promise<SecurityScanItem>;
}

export async function getScan(projectId: string, scanId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/security/scans/${scanId}`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error("Failed to get scan");
  return res.json() as Promise<SecurityScanItem>;
}
