import {
  currentUserApiV1AuthMeGet,
  loginApiV1AuthLoginPost,
  logoutApiV1AuthLogoutPost,
  type LoginRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function login(credentials: LoginRequest) {
  const { data } = await loginApiV1AuthLoginPost({
    body: credentials,
    client: apiClient,
    throwOnError: true,
  });
  return data;
}

export async function getCurrentUser() {
  const { data } = await currentUserApiV1AuthMeGet({
    client: apiClient,
    throwOnError: true,
  });
  return data;
}

export async function logout() {
  await logoutApiV1AuthLogoutPost({
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
}
