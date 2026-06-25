import { createClient as createFetchClient } from "./client/client";

export * from "./client";

export function createClient(baseUrl: string) {
  return createFetchClient({
    baseUrl,
    credentials: "include",
  });
}
