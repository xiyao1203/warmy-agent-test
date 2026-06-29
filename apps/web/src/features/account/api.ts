import {
  currentUserApiV1AuthMeGet,
  updateProfileApiV1AuthMePatch,
  changePasswordApiV1AuthChangePasswordPost,
  getSettingsApiV1UsersMeSettingsGet,
  updateSettingsApiV1UsersMeSettingsPatch,
  createFeedbackApiV1FeedbackPost,
  type UpdateProfileRequest,
  type ChangePasswordRequest,
  type UpdateSettingsRequest,
  type CreateFeedbackRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/api/csrf";

export async function getCurrentUser() {
  const { data } = await currentUserApiV1AuthMeGet({
    client: apiClient,
    throwOnError: true,
  });
  return data;
}

export async function updateProfile(body: UpdateProfileRequest) {
  const { data } = await updateProfileApiV1AuthMePatch({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
  return data;
}

export async function changePassword(body: ChangePasswordRequest) {
  await changePasswordApiV1AuthChangePasswordPost({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
}

export async function getUserSettings() {
  const { data } = await getSettingsApiV1UsersMeSettingsGet({
    client: apiClient,
    throwOnError: true,
  });
  return data;
}

export async function updateUserSettings(body: UpdateSettingsRequest) {
  const { data } = await updateSettingsApiV1UsersMeSettingsPatch({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
  return data;
}

export async function submitFeedback(body: CreateFeedbackRequest) {
  const { data } = await createFeedbackApiV1FeedbackPost({
    body,
    client: apiClient,
    throwOnError: true,
  });
  return data;
}
