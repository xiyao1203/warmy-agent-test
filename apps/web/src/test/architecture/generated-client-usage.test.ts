import { readFileSync } from "node:fs";
import { globSync } from "node:fs";

import { describe, expect, it } from "vitest";

const RAW_FETCH_MARKER = "raw-fetch-allowed:";

describe("generated Control API client ownership", () => {
  it("requires an audited streaming or download reason for every raw fetch", () => {
    const violations: string[] = [];
    for (const file of globSync("src/features/**/*.{ts,tsx}")) {
      const lines = readFileSync(file, "utf8").split("\n");
      lines.forEach((line, index) => {
        if (!/\bfetch\s*\(/.test(line)) return;
        const context = lines
          .slice(Math.max(0, index - 2), index + 1)
          .join(" ");
        if (!context.includes(RAW_FETCH_MARKER)) {
          violations.push(`${file}:${index + 1}`);
        }
      });
    }

    expect(violations).toEqual([]);
  });
});
