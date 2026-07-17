import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export type GateItem = GateSummaryResponse;

export type GateResult = {
  passed: boolean;
  failures: string[];
};

export type GateRun = Pick<RunResponse, "created_at" | "id" | "status">;

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
    run_id: string;
    experiment_id?: string | null;
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

export async function listGateRuns(projectId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/runs?limit=50`,
    { credentials: "include" },
  );
  if (!res.ok) throw await responseProblem(res, "加载执行记录失败");
  const data = await res.json();
  return data.items as GateRun[];
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
import type {
  GateSummaryResponse,
  RunResponse,
} from "@warmy/generated-api-client";
