import { createClient } from "@warmy/generated-api-client";

export const apiClient = createClient(
  process.env.NEXT_PUBLIC_CONTROL_API_URL ?? "http://localhost:8000",
);
