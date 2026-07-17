import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("GLM workspace design tokens", () => {
  const tokens = readFileSync(
    resolve(process.cwd(), "src/styles/tokens.css"),
    "utf8",
  );

  it("defines coral product accents and workspace density tokens", () => {
    expect(tokens).toContain("--primary: #e94b43");
    expect(tokens).toContain("--control-height-sm: 32px");
    expect(tokens).toContain("--sidebar-width: 240px");
    expect(tokens).toContain("--shadow-overlay:");
  });

  it("defines a complete explicit dark theme", () => {
    expect(tokens).toMatch(/\.dark\s*\{/);
    expect(tokens).toContain("--canvas: #111113");
    expect(tokens).toContain("--primary: #ff6b61");
  });
});
