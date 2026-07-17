import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { buildBundleReport } from "./report_web_bundles.mjs";

export function findBudgetViolations(
  report,
  baseline,
  { maxChunkGzipBytes = 256000, maxRegressionRatio = 0.05 } = {},
) {
  const violations = [];
  for (const [route, expected] of Object.entries(
    baseline.routes ?? {},
  ).sort()) {
    const actual = report.routes?.[route];
    if (!actual) {
      violations.push(
        `${route}: route is missing from the current bundle report`,
      );
      continue;
    }
    const limit = Math.floor(expected.gzipBytes * (1 + maxRegressionRatio));
    if (actual.gzipBytes > limit) {
      violations.push(
        `${route}: gzip bytes ${actual.gzipBytes} exceed budget ${limit} (baseline ${expected.gzipBytes})`,
      );
    }
  }
  for (const [name, size] of Object.entries(report.chunks ?? {}).sort()) {
    if (size.gzipBytes > maxChunkGzipBytes) {
      violations.push(
        `${name}: gzip bytes ${size.gzipBytes} exceed synchronous chunk budget ${maxChunkGzipBytes}`,
      );
    }
  }
  return violations;
}

async function main() {
  const [nextDir, baselinePath] = process.argv.slice(2);
  if (!nextDir || !baselinePath) {
    throw new Error(
      "Usage: check_web_bundle_budget.mjs <next-dir> <baseline-json>",
    );
  }
  const [report, baseline] = await Promise.all([
    buildBundleReport(nextDir),
    readFile(resolve(baselinePath), "utf8").then(JSON.parse),
  ]);
  const violations = findBudgetViolations(report, baseline);
  if (violations.length) {
    for (const violation of violations) process.stderr.write(`${violation}\n`);
    process.exitCode = 1;
    return;
  }
  process.stdout.write(
    `Bundle budgets passed for ${Object.keys(baseline.routes ?? {}).length} routes.\n`,
  );
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  await main();
}
