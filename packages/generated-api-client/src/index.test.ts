import { describe, expect, it } from "vitest";

import { createClient } from "./index.js";

describe("generated API client", () => {
  it("creates a client with the configured base URL", () => {
    const client = createClient("http://localhost:8000");

    expect(client).toBeDefined();
    expect(client.getConfig().baseUrl).toBe("http://localhost:8000");
  });
});
