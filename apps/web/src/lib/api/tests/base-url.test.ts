import { describe, expect, it } from "vitest";

import { resolveControlApiUrl } from "../base-url";

describe("resolveControlApiUrl", () => {
  it("uses same-origin requests in production when no external API is configured", () => {
    expect(resolveControlApiUrl({ NODE_ENV: "production" })).toBe("");
  });

  it("normalizes an explicitly configured API URL", () => {
    expect(
      resolveControlApiUrl({
        NODE_ENV: "production",
        NEXT_PUBLIC_CONTROL_API_URL: "https://control.example.com/",
      }),
    ).toBe("https://control.example.com");
  });

  it("keeps the documented localhost default outside production", () => {
    expect(resolveControlApiUrl({ NODE_ENV: "test" })).toBe(
      "http://localhost:8181",
    );
  });
});
