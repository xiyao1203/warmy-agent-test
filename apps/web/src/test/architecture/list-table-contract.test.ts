import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import ts from "typescript";
import { describe, expect, it } from "vitest";

const resourceLists = [
  "features/projects/project-list-screen.tsx",
  "features/projects/project-overview.tsx",
  "features/agents/agent-list.tsx",
  "features/datasets/dataset-list.tsx",
  "features/datasets/dataset-detail.tsx",
  "features/test-plans/test-plan-list.tsx",
  "features/runs/run-center.tsx",
  "features/environments/environment-list.tsx",
  "features/browser-profiles/browser-profile-list.tsx",
  "features/model-configs/model-config-list.tsx",
  "features/test-accounts/test-account-list.tsx",
  "features/users/user-management.tsx",
  "features/scorers/scorer-list.tsx",
  "features/experiments/experiment-list.tsx",
  "features/reviews/review-workbench.tsx",
  "features/security/security-scan.tsx",
  "features/gates/gate-list.tsx",
] as const;

const paginatedManagementLists = [
  "features/projects/project-list-screen.tsx",
  "features/agents/agent-list.tsx",
  "features/datasets/dataset-list.tsx",
  "features/test-plans/test-plan-list.tsx",
  "features/runs/run-center.tsx",
  "features/environments/environment-list.tsx",
  "features/browser-profiles/browser-profile-list.tsx",
  "features/model-configs/model-config-list.tsx",
  "features/test-accounts/test-account-list.tsx",
  "features/users/user-management.tsx",
  "features/scorers/scorer-list.tsx",
  "features/experiments/experiment-list.tsx",
  "features/reviews/review-workbench.tsx",
  "features/security/security-scan.tsx",
  "features/gates/gate-list.tsx",
] as const;

const internalCopySurfaces = [
  "features/auth/login-screen.tsx",
  "features/projects/project-overview.tsx",
  "app/(help)/docs/tutorials/page.tsx",
] as const;

function source(relativePath: string) {
  return readFileSync(resolve(process.cwd(), "src", relativePath), "utf8");
}

function jsxTagName(node: ts.JsxElement) {
  return node.openingElement.tagName.getText();
}

function nodeContainsJsx(node: ts.Node) {
  let found = false;
  function visit(child: ts.Node) {
    if (
      ts.isJsxElement(child) ||
      ts.isJsxFragment(child) ||
      ts.isJsxSelfClosingElement(child)
    ) {
      found = true;
      return;
    }
    ts.forEachChild(child, visit);
  }
  visit(node);
  return found;
}

function childHasVisibleText(child: ts.JsxChild): boolean {
  if (ts.isJsxText(child)) return child.text.trim().length > 0;
  if (ts.isJsxExpression(child)) {
    return Boolean(child.expression && !nodeContainsJsx(child.expression));
  }
  if (ts.isJsxElement(child) || ts.isJsxFragment(child)) {
    return child.children.some(childHasVisibleText);
  }
  return false;
}

function hasJsxAncestor(node: ts.Node, names: ReadonlySet<string>) {
  let current = node.parent;
  while (current) {
    if (ts.isJsxElement(current) && names.has(jsxTagName(current))) return true;
    current = current.parent;
  }
  return false;
}

function findRawIconOnlyTableButtons(file: string, contents: string) {
  const sourceFile = ts.createSourceFile(
    file,
    contents,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const violations: string[] = [];

  function visit(node: ts.Node) {
    if (ts.isJsxElement(node)) {
      const tagName = jsxTagName(node);
      const isButton = tagName === "Button" || tagName === "button";
      const isInTableSection = hasJsxAncestor(
        node,
        new Set(["TableCell", "TableHead"]),
      );
      const hasIcon = node.children.some(nodeContainsJsx);
      const hasVisibleText = node.children.some(childHasVisibleText);
      const hasTooltip = hasJsxAncestor(node, new Set(["Tooltip"]));
      if (
        isButton &&
        isInTableSection &&
        hasIcon &&
        !hasVisibleText &&
        !hasTooltip
      ) {
        const { line } = sourceFile.getLineAndCharacterOfPosition(
          node.getStart(sourceFile),
        );
        violations.push(`${file}:${line + 1} raw icon-only table button`);
      }
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return violations;
}

describe("resource list table contract", () => {
  it("uses the shared standard pagination on every management list", () => {
    const violations = paginatedManagementLists
      .filter((file) => !source(file).includes("ResourcePagination"))
      .map((file) => `${file}: missing shared pagination`);

    expect(violations).toEqual([]);
  });

  it("detects unwrapped shared icon buttons as contract violations", () => {
    expect(
      findRawIconOnlyTableButtons(
        "synthetic.tsx",
        '<TableCell><Button aria-label="查看"><Eye className="size-4" /></Button></TableCell>',
      ),
    ).toEqual(["synthetic.tsx:1 raw icon-only table button"]);
    expect(
      findRawIconOnlyTableButtons(
        "synthetic.tsx",
        '<TableCell><Tooltip content="查看"><Button aria-label="查看"><Eye className="size-4" /></Button></Tooltip></TableCell>',
      ),
    ).toEqual([]);
  });

  it("uses content-driven columns instead of fixed percentage layouts", () => {
    const violations = resourceLists.flatMap((file) => {
      const contents = source(file);
      const findings: string[] = [];
      if (/\btable-fixed\b/.test(contents))
        findings.push(`${file}: table-fixed`);
      if (/w-\[\d+%\]/.test(contents))
        findings.push(`${file}: percentage width`);
      return findings;
    });

    expect(violations).toEqual([]);
  });

  it("keeps resource names out of concise action tooltip labels", () => {
    const violations = resourceLists.flatMap((file) => {
      const contents = source(file);
      const actionTags = contents.match(/<TableActionButton[\s\S]*?>/g) ?? [];
      return actionTags.some((tag) => /\blabel=\{`[^`]*\$\{/.test(tag))
        ? [`${file}: interpolated TableActionButton label`]
        : [];
    });

    expect(violations).toEqual([]);
  });

  it("does not leave raw icon-only buttons in table headers or cells", () => {
    const violations = resourceLists.flatMap((file) =>
      findRawIconOnlyTableButtons(file, source(file)),
    );

    expect(violations).toEqual([]);
  });

  it("keeps internal design rationale out of product copy", () => {
    const prohibited = [
      "不展示桌面壳",
      "减少用户理解成本",
      "当前概览页只展示",
      "尚未接入的视频播放入口",
    ];
    const violations = internalCopySurfaces.flatMap((file) =>
      prohibited
        .filter((phrase) => source(file).includes(phrase))
        .map((phrase) => `${file}: ${phrase}`),
    );

    expect(violations).toEqual([]);
  });

  it("keeps the legacy stat card on the shared metric implementation", () => {
    const contents = source("components/uiverse/cards/stat-card.tsx");

    expect(contents).toContain("MetricCard");
    expect(contents).not.toContain("bg-[var(--primary-subtle)]");
  });

  it("keeps decorative AI effects out of visible product surfaces", () => {
    const semanticIconSurfaces = [
      "components/layout/app-shell-navigation.tsx",
      "components/uiverse/chat/markdown-content.tsx",
      "features/test-agent/context-panel.tsx",
    ];
    const iconViolations = semanticIconSurfaces.filter((file) =>
      source(file).includes("Sparkles"),
    );
    const login = source("features/auth/login-form.tsx");
    const glassCard = source("components/uiverse/cards/glass-card.tsx");
    const opaqueChrome = [
      "app/(account)/account/page.tsx",
      "features/help/help-shell.tsx",
    ];

    expect(iconViolations).toEqual([]);
    expect(login).not.toContain("PulseButton");
    expect(login).not.toContain("radius-pill");
    expect(glassCard).not.toMatch(/backdrop-blur|bg-white\//);
    expect(
      opaqueChrome.filter((file) => source(file).includes("backdrop-blur")),
    ).toEqual([]);
  });
});
