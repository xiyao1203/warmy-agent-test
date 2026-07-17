import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, relative, resolve, sep } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import ts from "../apps/web/node_modules/typescript/lib/typescript.js";

const SOURCE_EXTENSIONS = new Set([".ts", ".tsx"]);
const IGNORED_DIRECTORIES = new Set([".next", "coverage", "node_modules"]);

function sourceFiles(root) {
  const files = [];
  const visit = (path) => {
    for (const entry of readdirSync(path, { withFileTypes: true })) {
      if (entry.isDirectory() && IGNORED_DIRECTORIES.has(entry.name)) {
        continue;
      }
      const child = resolve(path, entry.name);
      if (entry.isDirectory()) {
        visit(child);
      } else if (SOURCE_EXTENSIONS.has(extname(entry.name))) {
        files.push(child);
      }
    }
  };
  if (statSync(root).isDirectory()) {
    visit(root);
  }
  return files.sort();
}

function featureFor(path) {
  const parts = path.split(sep);
  const index = parts.lastIndexOf("features");
  return index >= 0 ? parts[index + 1] : undefined;
}

function moduleSpecifiers(source, fileName) {
  const file = ts.createSourceFile(
    fileName,
    source,
    ts.ScriptTarget.Latest,
    true,
    fileName.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
  const values = [];
  const visit = (node) => {
    if (
      (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) &&
      node.moduleSpecifier &&
      ts.isStringLiteralLike(node.moduleSpecifier)
    ) {
      values.push(node.moduleSpecifier.text);
    } else if (
      ts.isCallExpression(node) &&
      node.arguments.length > 0 &&
      ts.isStringLiteralLike(node.arguments[0]) &&
      (node.expression.kind === ts.SyntaxKind.ImportKeyword ||
        (ts.isIdentifier(node.expression) &&
          ["require", "mock", "unmock"].includes(node.expression.text)) ||
        (ts.isPropertyAccessExpression(node.expression) &&
          ["mock", "unmock"].includes(node.expression.name.text)))
    ) {
      values.push(node.arguments[0].text);
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  return values;
}

export function findFrontendBoundaryViolations(root) {
  const absoluteRoot = resolve(root);
  const violations = new Set();
  for (const path of sourceFiles(absoluteRoot)) {
    const sourceFeature = featureFor(path);
    if (!sourceFeature) {
      continue;
    }
    const displayPath = relative(absoluteRoot, path).split(sep).join("/");
    for (const specifier of moduleSpecifiers(
      readFileSync(path, "utf8"),
      path,
    )) {
      const match = /^@\/features\/([^/]+)(?:\/(.+))?$/.exec(specifier);
      if (!match) {
        continue;
      }
      const [, targetFeature, internalPath] = match;
      if (targetFeature !== sourceFeature && internalPath) {
        violations.add(
          `${displayPath}: cross-Feature import must use @/features/${targetFeature}`,
        );
      }
    }
  }
  return [...violations].sort();
}

function main() {
  const roots = process.argv.slice(2);
  const targets = roots.length > 0 ? roots : ["apps/web/src"];
  const violations = targets.flatMap((root) =>
    findFrontendBoundaryViolations(root),
  );
  if (violations.length > 0) {
    process.stderr.write(`${violations.join("\n")}\n`);
    return 1;
  }
  process.stdout.write("Frontend Feature boundaries passed.\n");
  return 0;
}

if (
  process.argv[1] &&
  resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))
) {
  process.exitCode = main();
}
