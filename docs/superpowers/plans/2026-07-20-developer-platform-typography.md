# Developer Platform Typography Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Warmy Agent Test's legacy admin typography with a self-hosted Geist-based, seven-level semantic typography system that works consistently across Light and Dark themes without changing layout or business behavior.

**Architecture:** Load Geist, Geist Mono, and Noto Sans SC through `next/font/google` in the root layout, expose them as CSS variables, and map them into semantic typography tokens in `tokens.css`. Apply the tokens through global semantic classes and a narrow compatibility layer, then update shared UI components and representative page headings so the hierarchy is explicit rather than dependent on incidental Tailwind combinations.

**Tech Stack:** Next.js 16 App Router, React 19, `next/font/google`, Tailwind CSS 4, Vitest, Testing Library, Playwright.

---

### Task 1: Lock the font and typography token contract

**Files:**
- Modify: `apps/web/src/styles/tokens.test.ts`
- Create: `apps/web/src/app/tests/typography-layout.test.ts`
- Modify: `apps/web/src/app/layout.tsx`
- Modify: `apps/web/src/styles/tokens.css`

- [x] **Step 1: Write the failing root-font contract test**

Create a source-level test that reads `src/app/layout.tsx` and requires the three Next Font imports, stable CSS variable names, and the root class assignment:

```ts
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("root typography fonts", () => {
  const layout = readFileSync(resolve(process.cwd(), "src/app/layout.tsx"), "utf8");

  it("self-hosts the UI, Chinese fallback, and technical fonts", () => {
    expect(layout).toContain(
      'import { Geist, Geist_Mono, Noto_Sans_SC } from "next/font/google"',
    );
    expect(layout).toContain('variable: "--font-geist"');
    expect(layout).toContain('variable: "--font-geist-mono"');
    expect(layout).toContain('variable: "--font-noto-sans-sc"');
    expect(layout).toContain("geist.variable");
    expect(layout).toContain("geistMono.variable");
    expect(layout).toContain("notoSansSc.variable");
  });
});
```

- [x] **Step 2: Extend the token test with the exact seven-level contract**

Add assertions for the font stacks, exact typography values, exact Light/Dark text colors, tabular numbers, and code ligature handling:

```ts
it("defines the approved developer-platform typography system", () => {
  expect(tokens).toContain('--font-sans: var(--font-geist), "Source Han Sans SC"');
  expect(tokens).toContain('--font-code: var(--font-geist-mono), "Source Code Pro"');
  expect(tokens).toContain("--text-page-title-size: 26px");
  expect(tokens).toContain("--text-page-title-line-height: 36px");
  expect(tokens).toContain("--text-page-title-weight: 600");
  expect(tokens).toContain("--text-page-title-letter-spacing: -0.02em");
  expect(tokens).toContain("--text-section-title-size: 18px");
  expect(tokens).toContain("--text-section-title-line-height: 28px");
  expect(tokens).toContain("--text-card-title-size: 16px");
  expect(tokens).toContain("--text-card-title-line-height: 24px");
  expect(tokens).toContain("--text-body-size: 14px");
  expect(tokens).toContain("--text-body-line-height: 22px");
  expect(tokens).toContain("--text-secondary-size: 13px");
  expect(tokens).toContain("--text-secondary-line-height: 20px");
  expect(tokens).toContain("--text-caption-size: 12px");
  expect(tokens).toContain("--text-caption-line-height: 18px");
  expect(tokens).toContain("--text-code-size: 13px");
  expect(tokens).toContain("--text-code-line-height: 22px");
  expect(tokens).toContain("--ink: #101828");
  expect(tokens).toContain("--body: #344054");
  expect(tokens).toContain("--muted: #475467");
  expect(tokens).toContain("--muted-soft: #667085");
  expect(tokens).toContain("--ink: #F5F7FA");
  expect(tokens).toContain("--body: #D0D5DD");
  expect(tokens).toContain("--muted: #98A2B3");
  expect(globalStyles).toContain("font-variant-numeric: tabular-nums");
  expect(globalStyles).toContain("font-variant-ligatures: none");
});
```

- [x] **Step 3: Run the tests and verify RED**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/app/tests/typography-layout.test.ts src/styles/tokens.test.ts
```

Expected: FAIL because `layout.tsx` does not import Next Font and the approved typography/color tokens do not exist.

- [x] **Step 4: Implement the root fonts and token values**

In `layout.tsx`, instantiate the fonts and attach their variables to `<html>`:

```tsx
import { Geist, Geist_Mono, Noto_Sans_SC } from "next/font/google";

const geist = Geist({
  display: "swap",
  subsets: ["latin"],
  variable: "--font-geist",
});
const geistMono = Geist_Mono({
  display: "swap",
  subsets: ["latin"],
  variable: "--font-geist-mono",
});
const notoSansSc = Noto_Sans_SC({
  display: "swap",
  subsets: ["latin"],
  variable: "--font-noto-sans-sc",
  weight: ["400", "500", "600"],
});

<html
  className={`${geist.variable} ${geistMono.variable} ${notoSansSc.variable}`}
  lang="zh-CN"
  suppressHydrationWarning
>
```

In `tokens.css`, replace only the four text colors in each theme, define `--font-sans`, `--font-code`, and the seven semantic typography token groups. Keep all brand, status, surface, border, and layout tokens unchanged.

- [x] **Step 5: Run the focused tests and verify GREEN**

Run the same Vitest command. Expected: 2 files pass with no warnings.

- [x] **Step 6: Commit the font delivery and token contract**

```bash
git add apps/web/src/app/layout.tsx apps/web/src/app/tests/typography-layout.test.ts apps/web/src/styles/tokens.css apps/web/src/styles/tokens.test.ts
git commit -m "feat(web): establish developer platform typography tokens"
```

### Task 2: Add semantic typography utilities and the compatibility layer

**Files:**
- Modify: `apps/web/src/styles/tokens.test.ts`
- Modify: `apps/web/src/app/globals.css`

- [x] **Step 1: Write failing assertions for all semantic utilities**

Require `.text-page-title`, `.text-section-title`, `.text-card-title`, `.text-body`, `.text-secondary`, `.text-caption`, and `.text-code`, plus compatible `text-xs/sm/base/lg/2xl` line-height rules:

```ts
for (const semanticClass of [
  "text-page-title",
  "text-section-title",
  "text-card-title",
  "text-body",
  "text-secondary",
  "text-caption",
  "text-code",
]) {
  expect(globalStyles).toContain(`.${semanticClass}`);
}
expect(globalStyles).toMatch(/\.text-xs\s*\{[\s\S]*?font-size: var\(--text-caption-size\)/);
expect(globalStyles).toMatch(/\.text-sm\s*\{[\s\S]*?font-size: var\(--text-body-size\)/);
expect(globalStyles).toMatch(/\.text-base\s*\{[\s\S]*?font-size: var\(--text-card-title-size\)/);
expect(globalStyles).toMatch(/\.text-lg\s*\{[\s\S]*?font-size: var\(--text-section-title-size\)/);
expect(globalStyles).toMatch(/\.text-2xl\s*\{[\s\S]*?font-size: var\(--text-page-title-size\)/);
```

- [x] **Step 2: Run the token test and verify RED**

Run `pnpm --filter @warmy/web exec vitest run src/styles/tokens.test.ts`.

Expected: FAIL because the semantic and compatibility classes are absent.

- [x] **Step 3: Implement the semantic classes**

Add stable classes after the base element rules in `globals.css`. Each class must use its matching size, weight, line-height, and letter-spacing token. `.text-code` also uses `var(--font-code)` and disables ligatures.

Add a narrow compatibility layer for only `text-xs`, `text-sm`, `text-base`, `text-lg`, and `text-2xl`; do not alter spacing, control dimensions, or display typography above 26px. Keep the landing Hero's explicit large classes intact.

- [x] **Step 4: Run the token test and verify GREEN**

Run `pnpm --filter @warmy/web exec vitest run src/styles/tokens.test.ts`.

Expected: the token suite passes.

- [x] **Step 5: Commit the utility layer**

```bash
git add apps/web/src/app/globals.css apps/web/src/styles/tokens.test.ts
git commit -m "feat(web): add semantic typography utilities"
```

### Task 3: Apply component typography contracts

**Files:**
- Modify: `apps/web/src/components/ui/button.tsx`
- Create: `apps/web/src/components/ui/button.test.tsx`
- Modify: `apps/web/src/components/ui/badge.tsx`
- Create: `apps/web/src/components/ui/badge.test.tsx`
- Modify: `apps/web/src/components/ui/table.tsx`
- Modify: `apps/web/src/components/ui/table.test.tsx`
- Modify: `apps/web/src/components/layout/app-shell.test.tsx`
- Modify: `apps/web/src/app/globals.css`

- [x] **Step 1: Write failing component tests**

Require Button to use `text-button`, Badge to use `text-badge`, Table Head to use `text-table-head`, Table Cell to use `text-table-cell`, and navigation to expose the approved normal/active/category classes through its existing CSS hooks. Component roles prevent CSS cascade order from weakening their required weights.

```tsx
expect(screen.getByRole("button", { name: "新建" })).toHaveClass(
  "text-button",
);
expect(screen.getByText("已启用")).toHaveClass("text-badge");
expect(screen.getByRole("columnheader", { name: "模型" })).toHaveClass(
  "text-table-head",
);
expect(screen.getByRole("cell", { name: "gpt-5.5" })).toHaveClass(
  "text-table-cell",
);
```

Extend the shell contract to require `.app-nav-label` to use the caption token, `.app-nav-link` to use body size/400, and active links to use 600.

- [x] **Step 2: Run focused tests and verify RED**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/button.test.tsx src/components/ui/badge.test.tsx src/components/ui/table.test.tsx src/components/layout/app-shell.test.tsx
```

Expected: FAIL on the new semantic class assertions.

- [x] **Step 3: Apply the component classes without layout changes**

- Button: replace `text-sm font-medium` with `text-button` (14px / 600 / 22px).
- Badge: replace the 11px arbitrary size with `text-badge` (12px / 500 / 18px); retain current padding, radius, and tones.
- Table: apply `text-table-cell` (14px / 400 / 22px) to cells and `text-table-head` (13px / 500 / 20px) to headers; retain existing 36px header and 44px row heights.
- Sidebar CSS: use the body/caption typography tokens while retaining 34px navigation rows, 208px/56px widths, icons, colors, and hover motion.

- [x] **Step 4: Run focused tests and verify GREEN**

Run the same four-file Vitest command. Expected: all focused tests pass.

- [x] **Step 5: Commit shared component typography**

```bash
git add apps/web/src/components/ui/button.tsx apps/web/src/components/ui/button.test.tsx apps/web/src/components/ui/badge.tsx apps/web/src/components/ui/badge.test.tsx apps/web/src/components/ui/table.tsx apps/web/src/components/ui/table.test.tsx apps/web/src/components/layout/app-shell.test.tsx apps/web/src/app/globals.css
git commit -m "feat(web): align shared components with typography system"
```

### Task 4: Make page hierarchy and technical content semantic

**Files:**
- Create: `apps/web/src/test/architecture/typography-contract.test.ts`
- Modify: primary page-title files under `apps/web/src/features/**`
- Modify: technical-content files under `apps/web/src/features/runs/**`, `apps/web/src/features/test-agent/**`, and shared Markdown/code renderers

- [x] **Step 1: Write the failing architecture contract**

Create a test with an explicit allowlist of primary platform screens and require their main page heading to use `text-page-title`. The allowlist includes account, agent list/detail, browser profiles, datasets list/detail, environments, experiments, gates, model configs, projects, reviews, runs list/detail, scorers, security, test plans list/detail, and user management.

The same test scans production TSX for `font-mono` and requires technical surfaces to use `text-code` alongside it, except compact IDs that intentionally remain Caption-sized.

```ts
for (const file of pageTitleFiles) {
  const source = readFileSync(resolve(process.cwd(), "src", file), "utf8");
  expect(source, file).toMatch(/<h1[^>]*className="[^"]*text-page-title/);
}
```

- [x] **Step 2: Run the architecture test and verify RED**

Run `pnpm --filter @warmy/web exec vitest run src/test/architecture/typography-contract.test.ts`.

Expected: FAIL listing the screens still using incidental `text-2xl font-semibold tracking-tight` combinations.

- [x] **Step 3: Migrate only semantic text roles**

- Replace primary workspace `h1` combinations with `text-page-title`.
- Replace explicit 18px section headings with `text-section-title` when they are actual section headers.
- Replace panel/card headings with `text-card-title` where shared layout classes do not already supply the role.
- Replace page descriptions with `text-body` or `text-secondary` according to the approved hierarchy.
- Add `text-code` to Prompt, JSON, API, Trace, Log, execution-detail, and Token-statistic containers while retaining overflow, truncation, syntax highlighting, and data flow.
- Do not modify Hero display-size classes, DOM structure, control dimensions, colors, or business logic.

- [x] **Step 4: Run the architecture test and verify GREEN**

Run the same Vitest command. Expected: the explicit page and technical-content contract passes.

- [x] **Step 5: Run representative component tests**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/features/projects/tests/project-list-screen.test.tsx src/features/runs/tests/run-result-workbench.test.tsx src/features/runs/tests/trace-tree.test.tsx src/features/auth/tests/login-screen.test.tsx
```

Expected: all representative landing, list, run, and trace tests pass.

- [x] **Step 6: Commit the semantic page migration**

```bash
git add apps/web/src/features apps/web/src/test/architecture/typography-contract.test.ts
git commit -m "refactor(web): apply semantic typography roles"
```

### Task 5: Verify computed typography in Light, Dark, and mobile layouts

**Files:**
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`
- Modify: `apps/web/tests/e2e/login.spec.ts`

- [x] **Step 1: Write failing Playwright computed-style assertions**

On the landing page and a representative workspace list page, assert:

```ts
await expect(page.locator("html")).toHaveCSS("font-family", /Geist/);
await expect(page.locator("h1").first()).toHaveCSS("font-size", "26px");
await expect(page.locator("h1").first()).toHaveCSS("line-height", "36px");
await expect(page.locator("h1").first()).toHaveCSS("font-weight", "600");
await expect(page.locator("thead th").first()).toHaveCSS("font-size", "13px");
await expect(page.locator("tbody td").first()).toHaveCSS("font-size", "14px");
```

For Light and Dark, assert the computed primary and body text RGB values corresponding to the approved hex values. At 390px, assert `document.documentElement.scrollWidth <= window.innerWidth` and that the page title/button text bounding boxes remain inside their containers.

- [x] **Step 2: Run the focused E2E tests and verify RED**

Run:

```bash
E2E_API_PORT=8320 E2E_WEB_PORT=5313 pnpm --filter @warmy/web exec playwright test tests/e2e/login.spec.ts tests/e2e/list-layout.spec.ts --grep "typography" --workers=1
```

Expected: FAIL until the new semantic classes and computed font stacks are active on the tested pages.

- [x] **Step 3: Fix only typography regressions revealed by E2E**

Adjust semantic class placement or typography tokens only. Do not change layout geometry, colors outside the four text tokens, or business behavior.

- [x] **Step 4: Re-run E2E and capture visual evidence**

Run the same command. Expected: all typography scenarios pass at desktop Light/Dark and 390px mobile, with screenshots saved by the existing Playwright artifact configuration.

- [x] **Step 5: Commit E2E coverage**

```bash
git add apps/web/tests/e2e/login.spec.ts apps/web/tests/e2e/list-layout.spec.ts
git commit -m "test(web): cover typography across themes and viewports"
```

### Task 6: Complete quality gates and repository records

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] **Step 1: Run the full frontend quality gate**

```bash
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
git diff --check
```

Expected: every command passes. Record exact test file/test counts and build page count from the actual output.

- [x] **Step 2: Inspect visual output**

Review Playwright screenshots for the landing page, model configuration/list page, Test Agent, and run center in Light/Dark at 1280/1440 and 390px. Confirm no clipped text, accidental wrapping, component resizing, or horizontal page scrolling.

- [x] **Step 3: Update repository records**

Move `TASK-20260720-010` from in-progress to completed, list the exact changed files, state that API/database/config/business behavior did not change, record every verification result, and set `docs/当前任务.md` to “当前无活动任务”. Keep the independent TapNow external validation note unchanged.

- [x] **Step 4: Commit the final records**

```bash
git add docs/当前任务.md docs/开发进度与变更记录.md
git commit -m "docs: record typography system completion"
```
