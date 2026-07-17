import { readFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

function normalizeChunkName(name) {
  return name.replace(/^\/_next\//, "");
}

function normalizeAppRoute(appPath) {
  const withoutGroups = appPath.replace(/\/\([^/]+\)/g, "");
  const withoutPage = withoutGroups.replace(/\/page$/, "");
  return withoutPage || "/";
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

async function appRouteChunks(nextDir) {
  let manifest;
  try {
    manifest = await readJson(join(nextDir, "server/app-paths-manifest.json"));
  } catch (error) {
    if (error?.code === "ENOENT") return {};
    throw error;
  }

  const routes = {};
  for (const [appPath, serverFile] of Object.entries(manifest)) {
    if (!appPath.endsWith("/page")) continue;
    const clientManifest = join(
      nextDir,
      "server",
      serverFile.replace(/\.js$/, "_client-reference-manifest.js"),
    );
    let source;
    try {
      source = await readFile(clientManifest, "utf8");
    } catch (error) {
      if (error?.code === "ENOENT") continue;
      throw error;
    }
    const chunks = Array.from(
      source.matchAll(/["']\/?_next\/(static\/chunks\/[^"']+\.js)["']/g),
      (match) => match[1],
    );
    routes[normalizeAppRoute(appPath)] = chunks;
  }
  return routes;
}

export async function buildBundleReport(nextDirInput) {
  const nextDir = resolve(nextDirInput);
  const manifest = await readJson(join(nextDir, "build-manifest.json"));
  const sharedChunks = [
    ...(manifest.polyfillFiles ?? []),
    ...(manifest.rootMainFiles ?? []),
  ];
  const routeFiles = {
    ...(manifest.pages ?? {}),
    ...(await appRouteChunks(nextDir)),
  };
  const routeChunks = Object.fromEntries(
    Object.entries(routeFiles)
      .filter(([route]) => route !== "/_app")
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([route, files]) => [
        route,
        Array.from(
          new Set([...sharedChunks, ...files].map(normalizeChunkName)),
        ).sort(),
      ]),
  );
  const chunkNames = Array.from(
    new Set(Object.values(routeChunks).flat()),
  ).sort();
  const chunks = {};
  for (const name of chunkNames) {
    const content = await readFile(join(nextDir, name));
    chunks[name] = {
      gzipBytes: gzipSync(content).byteLength,
      rawBytes: content.byteLength,
    };
  }
  const routes = {};
  for (const [route, names] of Object.entries(routeChunks)) {
    routes[route] = {
      chunks: names,
      gzipBytes: names.reduce(
        (total, name) => total + chunks[name].gzipBytes,
        0,
      ),
      rawBytes: names.reduce((total, name) => total + chunks[name].rawBytes, 0),
    };
  }
  return { schemaVersion: 1, chunks, routes };
}

async function main() {
  const nextDir = process.argv[2];
  if (!nextDir) throw new Error("Usage: report_web_bundles.mjs <next-dir>");
  process.stdout.write(
    `${JSON.stringify(await buildBundleReport(nextDir), null, 2)}\n`,
  );
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  await main();
}
