import { describe, expect, it } from "vitest";

import { metadata } from "../layout";

describe("root layout metadata", () => {
  it("uses the Warmy Agent Test product name in metadata", () => {
    expect(metadata.title).toBe("Warmy Agent Test");
  });
});
