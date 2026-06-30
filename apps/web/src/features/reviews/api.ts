import { CONTROL_API_URL as API_BASE } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";

export type ReviewTask = {
  id: string;
  project_id: string;
  run_case_id: string;
  status: string;
  confidence: number;
  reviewer_id: string | null;
  score: number | null;
  opinion: string | null;
  rubric_scores: Record<string, number> | null;
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
};

export async function listReviews(projectId: string, status?: string) {
  const params = new URLSearchParams({ limit: "100" });
  if (status) params.set("status", status);
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/reviews?${params}`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error("Failed to list reviews");
  const data = await res.json();
  return data.items as ReviewTask[];
}

export async function scoreReview(
  projectId: string,
  taskId: string,
  payload: {
    score: number;
    opinion?: string;
    rubric_scores?: Record<string, number>;
  },
) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/reviews/${taskId}/score`,
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
  if (!res.ok) throw new Error("Failed to score review");
  return res.json() as Promise<ReviewTask>;
}

export async function rejectReview(
  projectId: string,
  taskId: string,
  opinion?: string,
) {
  const params = opinion ? `?opinion=${encodeURIComponent(opinion)}` : "";
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/reviews/${taskId}/reject${params}`,
    {
      method: "POST",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!res.ok) throw new Error("Failed to reject review");
  return res.json() as Promise<ReviewTask>;
}

export async function skipReview(projectId: string, taskId: string) {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/reviews/${taskId}/skip`,
    {
      method: "POST",
      headers: csrfHeaders() as Record<string, string>,
      credentials: "include",
    },
  );
  if (!res.ok) throw new Error("Failed to skip review");
  return res.json() as Promise<ReviewTask>;
}
