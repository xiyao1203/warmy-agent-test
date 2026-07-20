import {
  createUserApiV1SystemUsersPost,
  deleteUserApiV1SystemUsersUserIdDelete,
  disableUserApiV1SystemUsersUserIdDisablePost,
  enableUserApiV1SystemUsersUserIdEnablePost,
  listUsersApiV1SystemUsersGet,
  resetPasswordApiV1SystemUsersUserIdResetPasswordPost,
  updateUserApiV1SystemUsersUserIdPatch,
  type CreateUserRequest,
  type UpdateUserRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function listUsers(page = 1, pageSize = 10) {
  const { data } = await listUsersApiV1SystemUsersGet({
    client: apiClient,
    query: { page, page_size: pageSize },
    throwOnError: true,
  });
  return data;
}

export async function createUser(payload: CreateUserRequest) {
  const { data } = await createUserApiV1SystemUsersPost({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
  return data;
}

export async function updateUser(userId: string, payload: UpdateUserRequest) {
  const { data } = await updateUserApiV1SystemUsersUserIdPatch({
    body: payload,
    client: apiClient,
    headers: csrfHeaders(),
    path: { user_id: userId },
    throwOnError: true,
  });
  return data;
}

export async function resetUserPassword(userId: string, newPassword: string) {
  await resetPasswordApiV1SystemUsersUserIdResetPasswordPost({
    body: { new_password: newPassword },
    client: apiClient,
    headers: csrfHeaders(),
    path: { user_id: userId },
    throwOnError: true,
  });
}

export async function setUserEnabled(userId: string, enabled: boolean) {
  const method = enabled
    ? enableUserApiV1SystemUsersUserIdEnablePost
    : disableUserApiV1SystemUsersUserIdDisablePost;
  const { data } = await method({
    client: apiClient,
    headers: csrfHeaders(),
    path: { user_id: userId },
    throwOnError: true,
  });
  return data;
}

export async function deleteUser(userId: string) {
  await deleteUserApiV1SystemUsersUserIdDelete({
    client: apiClient,
    headers: csrfHeaders(),
    path: { user_id: userId },
    throwOnError: true,
  });
}
