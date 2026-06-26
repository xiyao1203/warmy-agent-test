import { describe, expect, it } from "vitest";

import { csrfHeaders, readCookie } from "./csrf";

describe("csrf helpers", () => {
  it("reads and decodes the CSRF cookie", () => {
    expect(readCookie("agenttest_csrf", "a=1; agenttest_csrf=hello%20world")).toBe(
      "hello world",
    );
  });

  it("adds the CSRF header for mutations", () => {
    expect(csrfHeaders("csrf-token")).toEqual({
      "x-csrf-token": "csrf-token",
    });
  });

  it("does not add an empty CSRF header", () => {
    expect(csrfHeaders(undefined)).toEqual({});
  });
});
