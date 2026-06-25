import { listUsersApiV1SystemUsersGet } from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";

export async function listUsers(cursor?: string | null) {
  const { data } = await listUsersApiV1SystemUsersGet({
    client: apiClient,
    query: { cursor, limit: 100 },
    throwOnError: true,
  });
  return data;
}
