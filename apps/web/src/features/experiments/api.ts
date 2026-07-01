import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

export type ExperimentItem = {
  id: string;
  project_id: string;
  name: string;
  run_a_id: string;
  run_b_id: string;
  status: string;
  result_json: Record<string, unknown>;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type ExperimentRun = {
  id: string;
  status: string;
  created_at: string;
  test_plan_version_id: string;
};

export async function listExperimentRuns(projectId: string) {
  const response = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/runs?limit=100`,
    { credentials: "include" },
  );
  if (!response.ok) throw await responseProblem(response, "加载执行记录失败");
  const data = await response.json();
  return (data.items as ExperimentRun[]).filter((run) =>
    ["passed", "failed", "error"].includes(run.status),
  );
}

export async function listExperiments(projectId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/experiments?limit=100`,
    { credentials: "include" },
  );
  if (!res.ok) throw await responseProblem(res, "加载实验失败");
  const data = await res.json();
  return data.items as ExperimentItem[];
}

export async function createExperiment(
  projectId: string,
  payload: {
    name: string;
    run_a_id: string;
    run_b_id: string;
    description?: string | null;
  },
) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/experiments`,
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
  if (!res.ok) throw await responseProblem(res, "创建实验失败");
  return res.json() as Promise<ExperimentItem>;
}

export async function getExperiment(projectId: string, experimentId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/experiments/${experimentId}`,
    { credentials: "include" },
  );
  if (!res.ok) throw await responseProblem(res, "加载实验详情失败");
  return res.json() as Promise<ExperimentItem>;
}

export async function runExperiment(projectId: string, experimentId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/experiments/${experimentId}/run`,
    {
      method: "POST",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!res.ok) throw await responseProblem(res, "运行实验失败");
  return res.json() as Promise<ExperimentItem>;
}
