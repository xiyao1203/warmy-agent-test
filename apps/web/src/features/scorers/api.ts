import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";

export type ScorerItem = {
  id: string;
  project_id: string;
  name: string;
  scorer_type: string;
  weight: number;
  threshold: number;
  config_json: Record<string, unknown>;
  description: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export async function listScorers(projectId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/scorers?limit=100`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error("Failed to list scorers");
  const data = await res.json();
  return data.items as ScorerItem[];
}

export async function createScorer(
  projectId: string,
  payload: {
    name: string;
    scorer_type: string;
    weight?: number;
    threshold?: number;
    config_json?: Record<string, unknown>;
    description?: string | null;
  },
) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/scorers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(csrfHeaders() as Record<string, string>),
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create scorer");
  return res.json() as Promise<ScorerItem>;
}

export async function updateScorer(
  projectId: string,
  scorerId: string,
  payload: {
    name?: string;
    weight?: number;
    threshold?: number;
    config_json?: Record<string, unknown>;
    description?: string | null;
    enabled?: boolean;
  },
) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/scorers/${scorerId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify(payload),
    },
  );
  if (!res.ok) throw new Error("Failed to update scorer");
  return res.json() as Promise<ScorerItem>;
}

export async function deleteScorer(projectId: string, scorerId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/scorers/${scorerId}`,
    {
      method: "DELETE",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!res.ok) throw new Error("Failed to delete scorer");
}
