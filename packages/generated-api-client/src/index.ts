import { createClient as createFetchClient } from "./client/client/index.js";

export * from "./client/index.js";

export function createClient(baseUrl: string) {
  return createFetchClient({
    baseUrl,
    credentials: "include",
  });
}
