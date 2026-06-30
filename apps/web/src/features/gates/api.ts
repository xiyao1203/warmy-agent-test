import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export type GateItem = {
  id: string;
  project_id: string;
  name: string;
  success_rate_threshold: number;
  critical_cases: string[];
  cost_limit: number | null;
  security_threshold: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type GateResult = {
  passed: boolean;
  failures: string[];
};

export async function listGates(projectId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/gates?limit=50`,
    { credentials: "include" },
  );
  if (!res.ok) throw await responseProblem(res, "加载门禁失败");
  const data = await res.json();
  return data.items as GateItem[];
}

export async function createGate(
  projectId: string,
  payload: {
    name: string;
    success_rate_threshold?: number;
    critical_cases?: string[];
    cost_limit?: number | null;
    security_threshold?: number;
  },
) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/gates`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(csrfHeaders() as Record<string, string>),
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await responseProblem(res, "创建门禁失败");
  return res.json() as Promise<GateItem>;
}

export async function evaluateGate(
  projectId: string,
  gateId: string,
  payload: {
    actual_pass_rate: number;
    critical_passed: boolean;
    actual_cost?: number | null;
    security_score?: number | null;
  },
) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/gates/${gateId}/evaluate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify(payload),
    },
  );
  if (!res.ok) throw await responseProblem(res, "评估门禁失败");
  return res.json() as Promise<{ gate_id: string; result: GateResult }>;
}

export async function deleteGate(projectId: string, gateId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/gates/${gateId}`,
    {
      method: "DELETE",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!res.ok) throw await responseProblem(res, "删除门禁失败");
}
