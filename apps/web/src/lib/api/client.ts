import { createClient } from "@warmy/generated-api-client";

import { CONTROL_API_URL } from "./base-url";

export const apiClient = createClient(CONTROL_API_URL);
