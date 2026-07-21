import { describe, expect, it, vi } from "vitest";

vi.mock("next/font/google", () => ({
  Geist: () => ({ variable: "font-geist" }),
  Geist_Mono: () => ({ variable: "font-geist-mono" }),
  Noto_Sans_SC: () => ({ variable: "font-noto-sans-sc" }),
}));

import { metadata } from "../layout";

describe("root layout metadata", () => {
  it("uses the Warmy Agent Test product name in metadata", () => {
    expect(metadata.title).toBe("Warmy Agent Test");
  });
});
