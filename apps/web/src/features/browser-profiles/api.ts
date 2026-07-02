import { apiClient } from "@/lib/api/client";
import { CONTROL_API_URL } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

// ── 类型 ─────────────────────────────────────────────────

export type BrowserProfile = {
  profile_id: string;
  project_id: string;
  name: string;
  target_domain: string;
  user_data_dir: string;
  storage_state_path: string;
  cdp_port: number;
  status: string;
  cdp_endpoint: string;
  created_at: string;
  updated_at: string;
};

// ── API ──────────────────────────────────────────────────

export async function listBrowserProfiles(
  projectId: string,
): Promise<BrowserProfile[]> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles`,
    { credentials: "include" },
  );
  if (!response.ok) throw await responseProblem(response, "加载浏览器实例失败");
  const data = await response.json();
  return (data.items ?? []) as BrowserProfile[];
}

export async function createBrowserProfile(
  projectId: string,
  payload: { name: string; target_domain?: string; user_data_dir?: string },
): Promise<BrowserProfile> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles`,
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
  if (!response.ok) throw await responseProblem(response, "创建浏览器实例失败");
  return response.json() as Promise<BrowserProfile>;
}

export async function updateBrowserProfile(
  projectId: string,
  profileId: string,
  payload: { name?: string; target_domain?: string },
): Promise<BrowserProfile> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles/${profileId}`,
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
  if (!response.ok) throw await responseProblem(response, "更新浏览器实例失败");
  return response.json() as Promise<BrowserProfile>;
}

export async function deleteBrowserProfile(
  projectId: string,
  profileId: string,
): Promise<void> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles/${profileId}`,
    {
      method: "DELETE",
      headers: {
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
    },
  );
  if (!response.ok) throw await responseProblem(response, "删除浏览器实例失败");
}
