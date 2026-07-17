import { createClient } from "@warmy/generated-api-client";

import { CONTROL_API_URL } from "./base-url";
import { normalizeGeneratedError } from "./problem";

export const apiClient = createClient(CONTROL_API_URL);

apiClient.interceptors.error.use((error, response) =>
  normalizeGeneratedError(error, response?.status ?? 0),
);
