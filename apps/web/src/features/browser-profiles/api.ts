import {
  completeLoginApiV1ProjectsProjectIdBrowserProfilesProfileIdLoginCompletePost,
  createProfileApiV1ProjectsProjectIdBrowserProfilesPost,
  deleteProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdDelete,
  listProfilesApiV1ProjectsProjectIdBrowserProfilesGet,
  startProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdStartPost,
  stopProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdStopPost,
  updateProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdPatch,
  verifyProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdVerifyPost,
  type CreateBrowserProfileRequest,
  type UpdateBrowserProfileRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";
import type { ResourcePage } from "@/lib/pagination";

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

const profilePath = (projectId: string, profileId: string) => ({
  profile_id: profileId,
  project_id: projectId,
});

export async function listBrowserProfiles(
  projectId: string,
  signal?: AbortSignal,
): Promise<BrowserProfile[]> {
  const { data } = await listProfilesApiV1ProjectsProjectIdBrowserProfilesGet({
    client: apiClient,
    path: { project_id: projectId },
    signal,
    throwOnError: true,
  });
  return (data as ResourcePage<BrowserProfile>).items;
}

export async function listBrowserProfilePage(
  projectId: string,
  signal?: AbortSignal,
  page = 1,
  pageSize = 10,
): Promise<ResourcePage<BrowserProfile>> {
  const { data } = await listProfilesApiV1ProjectsProjectIdBrowserProfilesGet({
    client: apiClient,
    path: { project_id: projectId },
    query: { page, page_size: pageSize },
    signal,
    throwOnError: true,
  });
  return data as ResourcePage<BrowserProfile>;
}

export async function createBrowserProfile(
  projectId: string,
  payload: CreateBrowserProfileRequest,
): Promise<BrowserProfile> {
  const { data } = await createProfileApiV1ProjectsProjectIdBrowserProfilesPost(
    {
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: { project_id: projectId },
      throwOnError: true,
    },
  );
  return data as BrowserProfile;
}

export async function updateBrowserProfile(
  projectId: string,
  profileId: string,
  payload: UpdateBrowserProfileRequest,
): Promise<BrowserProfile> {
  const { data } =
    await updateProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdPatch({
      body: payload,
      client: apiClient,
      headers: csrfHeaders(),
      path: profilePath(projectId, profileId),
      throwOnError: true,
    });
  return data as BrowserProfile;
}

export async function deleteBrowserProfile(
  projectId: string,
  profileId: string,
): Promise<void> {
  await deleteProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdDelete({
    client: apiClient,
    headers: csrfHeaders(),
    path: profilePath(projectId, profileId),
    throwOnError: true,
  });
}

export async function startBrowserProfile(
  projectId: string,
  profileId: string,
  payload: { login_url?: string },
): Promise<BrowserProfile> {
  const { data } =
    await startProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdStartPost({
      body: { login_url: payload.login_url ?? "" },
      client: apiClient,
      headers: csrfHeaders(),
      path: profilePath(projectId, profileId),
      throwOnError: true,
    });
  return data as BrowserProfile;
}

export async function completeBrowserProfileLogin(
  projectId: string,
  profileId: string,
  payload: { stop_after_save?: boolean } = {},
): Promise<BrowserProfile> {
  const { data } =
    await completeLoginApiV1ProjectsProjectIdBrowserProfilesProfileIdLoginCompletePost(
      {
        body: { stop_after_save: Boolean(payload.stop_after_save) },
        client: apiClient,
        headers: csrfHeaders(),
        path: profilePath(projectId, profileId),
        throwOnError: true,
      },
    );
  return data as BrowserProfile;
}

export async function stopBrowserProfile(
  projectId: string,
  profileId: string,
): Promise<BrowserProfile> {
  const { data } =
    await stopProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdStopPost({
      client: apiClient,
      headers: csrfHeaders(),
      path: profilePath(projectId, profileId),
      throwOnError: true,
    });
  return data as BrowserProfile;
}

export async function verifyBrowserProfile(
  projectId: string,
  profileId: string,
): Promise<BrowserProfile> {
  const { data } =
    await verifyProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdVerifyPost(
      {
        client: apiClient,
        headers: csrfHeaders(),
        path: profilePath(projectId, profileId),
        throwOnError: true,
      },
    );
  return data as BrowserProfile;
}
