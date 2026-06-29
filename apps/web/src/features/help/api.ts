import {
  createFeedbackApiV1FeedbackPost,
  type CreateFeedbackRequest,
} from "@warmy/generated-api-client";

import { apiClient } from "@/lib/api/client";

export async function submitFeedback(body: CreateFeedbackRequest) {
  const { data } = await createFeedbackApiV1FeedbackPost({
    body,
    client: apiClient,
    throwOnError: true,
  });
  return data;
}
