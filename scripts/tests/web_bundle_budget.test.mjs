import assert from "node:assert/strict";
import { gzipSync } from "node:zlib";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { buildBundleReport } from "../report_web_bundles.mjs";
import { findBudgetViolations } from "../check_web_bundle_budget.mjs";

async function bundleFixture() {
  const nextDir = await mkdtemp(join(tmpdir(), "agenttest-bundles-"));
  await mkdir(join(nextDir, "static/chunks"), { recursive: true });
  const chunks = {
    "static/chunks/a.js": "a".repeat(300),
    "static/chunks/b.js": "const answer = 42;".repeat(10),
    "static/chunks/runtime.js": "runtime".repeat(20),
  };
  for (const [name, content] of Object.entries(chunks)) {
    await writeFile(join(nextDir, name), content);
  }
  await writeFile(
    join(nextDir, "build-manifest.json"),
    JSON.stringify({
      pages: { "/login": ["static/chunks/b.js", "static/chunks/a.js"] },
      rootMainFiles: ["static/chunks/runtime.js", "static/chunks/a.js"],
    }),
  );
  return { chunks, nextDir };
}

test("reports deterministic de-duplicated raw and gzip route sizes", async (t) => {
  const { chunks, nextDir } = await bundleFixture();
  t.after(() => rm(nextDir, { force: true, recursive: true }));

  const report = await buildBundleReport(nextDir);
  const routeChunks = [
    "static/chunks/a.js",
    "static/chunks/b.js",
    "static/chunks/runtime.js",
  ];
  assert.deepEqual(report.routes["/login"], {
    chunks: routeChunks,
    gzipBytes: routeChunks.reduce(
      (total, name) => total + gzipSync(chunks[name]).byteLength,
      0,
    ),
    rawBytes: routeChunks.reduce(
      (total, name) => total + Buffer.byteLength(chunks[name]),
      0,
    ),
  });
  assert.deepEqual(Object.keys(report.chunks), routeChunks);
});

test("flags route regressions above five percent", () => {
  const baseline = {
    chunks: {},
    routes: { "/login": { chunks: [], gzipBytes: 100, rawBytes: 200 } },
  };

  assert.deepEqual(
    findBudgetViolations(
      {
        chunks: {},
        routes: { "/login": { chunks: [], gzipBytes: 105, rawBytes: 210 } },
      },
      baseline,
    ),
    [],
  );
  assert.match(
    findBudgetViolations(
      {
        chunks: {},
        routes: { "/login": { chunks: [], gzipBytes: 106, rawBytes: 212 } },
      },
      baseline,
    )[0],
    /\/login.*106.*105/,
  );
});

test("flags a synchronous chunk over 256000 gzip bytes", () => {
  const violations = findBudgetViolations(
    {
      chunks: {
        "static/chunks/huge.js": { gzipBytes: 256001, rawBytes: 300000 },
      },
      routes: {
        "/login": {
          chunks: ["static/chunks/huge.js"],
          gzipBytes: 256001,
          rawBytes: 300000,
        },
      },
    },
    { chunks: {}, routes: {} },
  );

  assert.equal(violations.length, 1);
  assert.match(violations[0], /huge\.js.*256001.*256000/);
});
