import { CONTROL_API_URL } from "@/lib/api/base-url";
import { csrfHeaders } from "@/lib/api/csrf";
import { responseProblem } from "@/lib/api/problem";

// ── 类型 ─────────────────────────────────────────────────

export type BrowserProfile = {
  profile_id: string;
  project_id: string;
  name: string;
  target_domain: string;
  status: string;
  auth_state_status: "missing" | "ready" | "expired" | "error";
  auth_state_version: number;
  auth_state_updated_at: string | null;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
  last_verified_at: string | null;
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
  payload: { name: string; target_domain?: string },
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

export async function startBrowserProfile(
  projectId: string,
  profileId: string,
  payload: { login_url?: string },
): Promise<BrowserProfile> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles/${profileId}/start`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify({ login_url: payload.login_url ?? "" }),
    },
  );
  if (!response.ok) throw await responseProblem(response, "启动浏览器失败");
  return response.json() as Promise<BrowserProfile>;
}

export async function completeBrowserProfileLogin(
  projectId: string,
  profileId: string,
  payload: { stop_after_save?: boolean } = {},
): Promise<BrowserProfile> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles/${profileId}/login-complete`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
      body: JSON.stringify({
        stop_after_save: Boolean(payload.stop_after_save),
      }),
    },
  );
  if (!response.ok) throw await responseProblem(response, "保存登录状态失败");
  return response.json() as Promise<BrowserProfile>;
}

export async function stopBrowserProfile(
  projectId: string,
  profileId: string,
): Promise<BrowserProfile> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles/${profileId}/stop`,
    {
      method: "POST",
      headers: {
        ...(csrfHeaders() as Record<string, string>),
      },
      credentials: "include",
    },
  );
  if (!response.ok) throw await responseProblem(response, "停止浏览器失败");
  return response.json() as Promise<BrowserProfile>;
}

export async function verifyBrowserProfile(
  projectId: string,
  profileId: string,
): Promise<BrowserProfile> {
  const response = await fetch(
    `${CONTROL_API_URL}/api/v1/projects/${projectId}/browser-profiles/${profileId}/verify`,
    {
      method: "POST",
      headers: { ...(csrfHeaders() as Record<string, string>) },
      credentials: "include",
    },
  );
  if (!response.ok) throw await responseProblem(response, "验证登录状态失败");
  return response.json() as Promise<BrowserProfile>;
}
