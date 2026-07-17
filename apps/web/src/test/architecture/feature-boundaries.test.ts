import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

// @ts-expect-error The repository scanner is a Node ESM script outside this package.
import { findFrontendBoundaryViolations } from "../../../../../scripts/check_frontend_boundaries.mjs";

const roots: string[] = [];

function fixture(relativePath: string, source: string): string {
  const root = mkdtempSync(join(tmpdir(), "feature-boundaries-"));
  roots.push(root);
  const path = join(root, relativePath);
  mkdirSync(join(path, ".."), { recursive: true });
  writeFileSync(path, source, "utf8");
  return root;
}

afterEach(() => {
  for (const root of roots.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

describe("frontend Feature boundaries", () => {
  it("rejects imports into another Feature's internals", () => {
    const root = fixture(
      "features/agents/editor.tsx",
      'import { listEnvironments } from "@/features/environments/api";\n',
    );

    expect(findFrontendBoundaryViolations(root)).toEqual([
      "features/agents/editor.tsx: cross-Feature import must use @/features/environments",
    ]);
  });

  it("accepts another Feature's public package export", () => {
    const root = fixture(
      "features/agents/editor.tsx",
      'import { listEnvironments } from "@/features/environments";\n',
    );

    expect(findFrontendBoundaryViolations(root)).toEqual([]);
  });
});
