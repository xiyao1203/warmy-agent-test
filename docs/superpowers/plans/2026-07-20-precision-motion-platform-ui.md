# Precision Motion Platform UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the landing page, application shell, shared component layer, metrics, lists, overlays, feedback, and core workspaces to the approved Precision Motion design without changing APIs, permissions, routes, pagination, or business behavior.

**Architecture:** Extend the existing semantic token layer and Radix/shadcn-style local primitives so Features inherit the new language without duplicating styles. Add shared compact state-edge metrics and inline feedback, then migrate the landing page, run center, user management, and project overview as reference implementations. Existing Feature ownership and generated API contracts remain unchanged.

**Tech Stack:** Next.js 16, React 19, TypeScript 6 strict mode, Tailwind CSS 4, Radix UI, lucide-react, TanStack Query, Vitest, Testing Library, Playwright.

---

## File Map

- Modify `apps/web/src/styles/{tokens.css,tokens.test.ts}` and `apps/web/src/app/globals.css` for the shared design and motion contract.
- Create `apps/web/src/components/ui/{metric-card,metric-card.test,inline-alert,inline-alert.test}.tsx`.
- Modify shared UI under `apps/web/src/components/ui` and `apps/web/src/components/uiverse` for buttons, lists, tables, menus, overlays, tooltips, hover summaries, and Toast.
- Modify `apps/web/src/components/layout/{app-shell,app-shell-navigation,app-shell.test}.tsx`.
- Modify `apps/web/src/features/auth/{login-screen,tests/login-screen.test}.tsx` and `apps/web/tests/e2e/login.spec.ts`.
- Modify run center, user management, and project overview components and tests.
- Modify help copy, `docs/design.md`, E2E coverage, current task, and progress records.

### Task 1: Register the branch, specification, plan, and clean baseline

**Files:**

- Create: `docs/superpowers/specs/2026-07-20-precision-motion-platform-ui-design.md`
- Create: `docs/superpowers/plans/2026-07-20-precision-motion-platform-ui.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] **Step 1: Create the implementation branch**

```bash
git switch -c codex/precision-motion-ui-overhaul
```

- [x] **Step 2: Verify the baseline**

```bash
pnpm --filter @warmy/web test
pnpm --filter @warmy/web typecheck
```

Expected: 94 test files / 347 tests pass and TypeScript exits 0.

- [x] **Step 3: Register the unique active task and approved design**

Expected: current-task and progress records contain the same task ID, branch, Web-only scope, exclusions, and baseline evidence.

- [ ] **Step 4: Commit planning artifacts**

```bash
git add docs/当前任务.md docs/开发进度与变更记录.md docs/superpowers/specs/2026-07-20-precision-motion-platform-ui-design.md docs/superpowers/plans/2026-07-20-precision-motion-platform-ui.md
git commit -m "docs: plan precision motion ui overhaul"
```

### Task 2: Lock the Precision Motion token contract

**Files:**

- Modify: `apps/web/src/styles/tokens.test.ts`
- Modify: `apps/web/src/styles/tokens.css`
- Modify: `apps/web/src/app/globals.css`

- [ ] **Step 1: Write failing token assertions**

```ts
it("defines compact navigation and semantic motion", () => {
  expect(tokens).toContain("--sidebar-width: 208px");
  expect(tokens).toContain("--sidebar-width-collapsed: 56px");
  expect(tokens).toContain("--navigation-row-height: 34px");
  expect(tokens).toContain("--metric-height: 88px");
  expect(tokens).toContain("--motion-dialog: 220ms");
  expect(tokens).toContain("--motion-drawer: 260ms");
});
```

- [ ] **Step 2: Verify RED**

```bash
pnpm --filter @warmy/web exec vitest run src/styles/tokens.test.ts
```

Expected: FAIL on the old 240px/60px sidebar and missing motion/metric tokens.

- [ ] **Step 3: Implement the tokens and reusable CSS states**

```css
--sidebar-width: 208px;
--sidebar-width-collapsed: 56px;
--navigation-row-height: 34px;
--icon-optical-size: 17px;
--icon-carrier-size: 24px;
--metric-height: 88px;
--metric-height-mobile: 84px;
--motion-micro: 120ms;
--motion-fast: 160ms;
--motion-standard: 180ms;
--motion-dialog: 220ms;
--motion-drawer: 260ms;
--motion-spatial: 280ms;
```

Set `--radius-lg` to 8px. Add named keyframes for menu, Dialog, Drawer, metric number, check path, alert tap, and running rotation, with Reduced Motion overrides.

- [ ] **Step 4: Verify GREEN and commit**

```bash
pnpm --filter @warmy/web exec vitest run src/styles/tokens.test.ts
pnpm --filter @warmy/web format
git add apps/web/src/styles apps/web/src/app/globals.css
git commit -m "style(web): define precision motion tokens"
```

### Task 3: Build compact metric and inline feedback primitives

**Files:**

- Create: `apps/web/src/components/ui/metric-card.tsx`
- Create: `apps/web/src/components/ui/metric-card.test.tsx`
- Create: `apps/web/src/components/ui/inline-alert.tsx`
- Create: `apps/web/src/components/ui/inline-alert.test.tsx`
- Modify: `apps/web/src/components/ui/summary-strip.tsx`

- [ ] **Step 1: Write failing MetricCard tests**

```tsx
render(
  <MetricCard
    action={<a href="/runs">查看</a>}
    change="+42"
    icon={<Activity />}
    label="全部运行"
    tone="accent"
    value="1,284"
  />,
);
expect(screen.getByRole("article", { name: "全部运行" })).toHaveAttribute(
  "data-tone",
  "accent",
);
expect(screen.getByRole("link", { name: "查看" })).toBeInTheDocument();
```

Add independent assertions for `loading`/`aria-busy`, `disabled`, `state="running"`, static cards without action, and stable labels.

- [ ] **Step 2: Write failing InlineAlert tests**

```tsx
render(
  <InlineAlert action={<button>重试</button>} title="运行启动失败" tone="danger">
    请检查运行服务后重试。
  </InlineAlert>,
);
expect(screen.getByRole("alert")).toHaveAttribute("data-tone", "danger");
expect(screen.getByRole("button", { name: "重试" })).toBeInTheDocument();
```

- [ ] **Step 3: Verify RED**

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/metric-card.test.tsx src/components/ui/inline-alert.test.tsx
```

Expected: FAIL because both modules are missing.

- [ ] **Step 4: Implement the primitives**

`MetricCard` accepts `label`, `value`, `icon`, `tone`, `state`, `change`, `action`, `loading`, and `disabled`, renders a fixed action slot, and exposes `data-tone`/`data-state`. `MetricGrid` owns the four-column/two-column layout. `MetricCardSkeleton` preserves exact height. `InlineAlert` renders a neutral body, semantic 2px edge, icon/title/body/action, and alert semantics for warning/danger. `SummaryStrip` becomes a compatibility wrapper over the metric grid.

- [ ] **Step 5: Verify GREEN and commit**

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/metric-card.test.tsx src/components/ui/inline-alert.test.tsx src/features/users/tests/user-management.test.tsx
git add apps/web/src/components/ui
git commit -m "feat(web): add precision metric and alert primitives"
```

### Task 4: Upgrade buttons, lists, menus, overlays, tooltips, and hover surfaces

**Files:**

- Modify: `apps/web/src/components/ui/{button,list-card,table,table-actions,dropdown-menu,dropdown-select,dialog,drawer}.tsx`
- Modify: `apps/web/src/components/ui/{dropdown-select,dialog,table-actions,table}.test.tsx`
- Modify: `apps/web/src/components/uiverse/feedback/{tooltip,toast}.tsx`
- Modify: `apps/web/src/components/uiverse/cards/hover-card.tsx`

- [ ] **Step 1: Add failing interaction assertions**

```tsx
fireEvent.pointerDown(screen.getByRole("button", { name: "状态：全部" }));
expect(screen.getByRole("menu")).toHaveClass("precision-menu-content");
expect(screen.getByRole("menu")).toHaveAttribute("data-side", "bottom");
```

Add assertions for stable 32px table actions, ListCard focus-within actions, Dialog focus restoration, Drawer semantic title, and Tooltip horizontal content.

- [ ] **Step 2: Verify RED**

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/dropdown-select.test.tsx src/components/ui/dialog.test.tsx src/components/ui/table-actions.test.tsx src/components/ui/table.test.tsx
```

- [ ] **Step 3: Implement the interaction layer**

Enable Radix collision handling with `collisionPadding={8}`. Apply state/side CSS animations to Dropdown, Dialog, and Drawer. Below 760px, Drawer enters from the bottom. Keep loading button dimensions stable, add a restrained pressed state, add optional semantic edge/icon/metrics to ListCard, keep table actions fixed, and make Toast a neutral body with a semantic edge. Tooltip remains short help; HoverCard remains resource summary; Artifact Preview stays in the Runs Feature.

- [ ] **Step 4: Verify GREEN and commit**

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/dropdown-select.test.tsx src/components/ui/dialog.test.tsx src/components/ui/table-actions.test.tsx src/components/ui/table.test.tsx
git add apps/web/src/components apps/web/src/app/globals.css
git commit -m "feat(web): refine interactive surfaces"
```

### Task 5: Narrow the shell and make navigation feedback explicit

**Files:**

- Modify: `apps/web/src/components/layout/app-shell.tsx`
- Modify: `apps/web/src/components/layout/app-shell-navigation.tsx`
- Modify: `apps/web/src/components/layout/app-shell.test.tsx`
- Modify: `apps/web/src/app/globals.css`

- [ ] **Step 1: Write failing shell assertions**

```tsx
expect(document.querySelector(".app-sidebar")).toHaveStyle({
  width: "var(--sidebar-width)",
});
expect(screen.getByRole("navigation", { name: "项目导航" })).not.toHaveTextContent(
  /通过率|运行数量|统计/,
);
```

Add a collapsed-state test that focuses a navigation link and observes its shared Tooltip label while the visible text is absent.

- [ ] **Step 2: Verify RED**

```bash
pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx
```

Expected: the shared Tooltip assertion fails because collapsed links still rely on native `title`.

- [ ] **Step 3: Implement the compact pure-navigation shell**

Use the 208px/56px tokens, 34px rows, 24px icon carriers, 17px icons, and 2px active rail. Use shared Tooltip when collapsed and remove native `title` reliance. Preserve project switching, permission-gated user management, mobile Drawer, command palette, and stored collapse preference.

- [ ] **Step 4: Verify GREEN and commit**

```bash
pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx src/components/layout/theme-toggle.test.tsx src/test/architecture/feature-boundaries.test.ts
git add apps/web/src/components/layout apps/web/src/app/globals.css
git commit -m "feat(web): tighten workspace navigation"
```

### Task 6: Rebuild the landing page and preserve post-login behavior

**Files:**

- Modify: `apps/web/src/features/auth/tests/login-screen.test.tsx`
- Modify: `apps/web/src/features/auth/login-screen.tsx`
- Modify: `apps/web/tests/e2e/login.spec.ts`

- [ ] **Step 1: Write failing landing behavior and copy tests**

```tsx
expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
  "Warmy Agent Test",
);
expect(screen.getByRole("link", { name: "查看运行证据" })).toHaveAttribute(
  "href",
  "#product-evidence",
);
expect(screen.queryByText(/不展示桌面壳|减少用户理解成本/)).not.toBeInTheDocument();
```

Keep the existing test proving successful login closes the Dialog without calling `router.push`, then assert the resulting “进入工作台” button navigates only on a later click.

- [ ] **Step 2: Verify RED**

```bash
pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx
```

Expected: FAIL on the old headline, button behavior, and internal copy.

- [ ] **Step 3: Implement the product-first landing page**

Replace the split hero and Sparkles eyebrow with a single-column `Warmy Agent Test` hero, business support copy, login/workspace primary action, and evidence anchor. Render a full-width product scene with a real run summary, execution list, evaluation evidence, review state, and gate status. Use full-width bands below the hero; do not add nested cards, fake customer logos, registration, pricing, gradients, glass, or internal design rationale.

- [ ] **Step 4: Verify component behavior**

```bash
pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx src/features/auth/tests/login-form.test.tsx src/app/tests/home-page-navigation.test.tsx
```

- [ ] **Step 5: Verify the landing E2E flow and commit**

```bash
pnpm --filter @warmy/web exec playwright test tests/e2e/login.spec.ts
git add apps/web/src/features/auth apps/web/tests/e2e/login.spec.ts
git commit -m "feat(web): rebuild product landing experience"
```

### Task 7: Migrate run center, user management, and project overview

**Files:**

- Modify: `apps/web/src/features/runs/run-center.tsx`
- Modify: `apps/web/src/features/runs/tests/run-center.test.tsx`
- Modify: `apps/web/src/features/users/user-management.tsx`
- Modify: `apps/web/src/features/users/tests/user-management.test.tsx`
- Modify: `apps/web/src/features/projects/project-overview.tsx`
- Modify: `apps/web/src/features/projects/tests/project-overview.test.tsx`

- [ ] **Step 1: Write failing shared-metric and copy assertions**

```tsx
expect(screen.getByRole("article", { name: "运行中" })).toHaveAttribute(
  "data-state",
  "running",
);
expect(screen.queryByText(/当前概览页只展示/)).not.toBeInTheDocument();
```

Add assertions for user metric labels, project metric icons without colored tiles, fixed metric actions, and RunCenter action errors rendered by `InlineAlert`.

- [ ] **Step 2: Verify RED**

```bash
pnpm --filter @warmy/web exec vitest run src/features/runs/tests/run-center.test.tsx src/features/users/tests/user-management.test.tsx src/features/projects/tests/project-overview.test.tsx
```

- [ ] **Step 3: Migrate the reference pages**

Replace RunCenter `SummaryCard` with `MetricGrid`/`MetricCard`, including running/check/alert states, and replace action-error text with `InlineAlert`. Replace user summary items with icon-aware metric cards while retaining filters and pagination. Replace project metrics with compact state-edge cards and rewrite the activity copy as direct business content.

- [ ] **Step 4: Verify GREEN and commit**

```bash
pnpm --filter @warmy/web exec vitest run src/features/runs/tests/run-center.test.tsx src/features/users/tests/user-management.test.tsx src/features/projects/tests/project-overview.test.tsx src/components/ui/resource-pagination.test.tsx
git add apps/web/src/features/runs apps/web/src/features/users apps/web/src/features/projects
git commit -m "feat(web): migrate core workspaces to precision metrics"
```

### Task 8: Converge remaining copy and legacy shared cards

**Files:**

- Modify: `apps/web/src/app/(help)/docs/tutorials/page.tsx`
- Modify: `apps/web/src/features/help/tests/help-pages.test.tsx`
- Modify: `apps/web/src/components/uiverse/cards/stat-card.tsx`
- Modify: `apps/web/src/components/uiverse/cards/hover-card.tsx`
- Modify: `apps/web/src/test/architecture/list-table-contract.test.ts`
- Modify: `docs/design.md`

- [ ] **Step 1: Add failing copy and legacy-card contract tests**

```ts
expect(screen.queryByText(/尚未接入的视频播放入口/)).not.toBeInTheDocument();
```

Add a source-level test that rejects the confirmed internal-rationale phrases in product `.tsx` files and rejects colored icon-tile styling in legacy `StatCard`.

- [ ] **Step 2: Verify RED**

```bash
pnpm --filter @warmy/web exec vitest run src/features/help/tests/help-pages.test.tsx src/test/architecture/list-table-contract.test.ts
```

- [ ] **Step 3: Remove internal rationale and align legacy exports**

Rewrite tutorial copy as available business content. Make legacy StatCard delegate to `MetricCard`; keep HoverCard as the resource-summary surface. Update `docs/design.md` with the final reference boundaries, dimensions, state rules, and component ownership.

- [ ] **Step 4: Scan, verify, and commit**

```bash
rg -n "不展示桌面壳|减少用户理解成本|当前概览页只展示|尚未接入的视频播放入口" apps/web/src
pnpm --filter @warmy/web test
git add apps/web/src docs/design.md
git commit -m "style(web): converge platform interaction language"
```

Expected: the source scan returns no matches and all Web tests pass.

### Task 9: Run responsive, accessibility, build, and bundle verification

**Files:**

- Modify: `apps/web/tests/e2e/login.spec.ts`
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Extend E2E design-contract assertions**

Cover 390/1280/1440/1920 widths, light/dark/system themes, landing first viewport, 208px/56px shell, collapsed Tooltip, metric two/four-column behavior, menu collision safety, Dialog/Drawer focus, and no page-level horizontal overflow.

- [ ] **Step 2: Run full Web quality checks**

```bash
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
```

- [ ] **Step 3: Run build and bundle budget**

```bash
pnpm --filter @warmy/web build
pnpm --filter @warmy/web perf:bundle-check
```

- [ ] **Step 4: Run critical Playwright E2E**

```bash
pnpm --filter @warmy/web e2e
```

Expected: local critical flows pass; only the existing credential-gated performance case may be conditionally skipped.

- [ ] **Step 5: Inspect actual screenshots and interaction states**

Start the local app and inspect landing, shell, run center, user management, project overview, Dropdown, Dialog, Drawer, Tooltip, Loading, empty, error, permission, and Reduced Motion states in the in-app browser. Confirm nonblank pixels and no text, control, or overlay overlap.

- [ ] **Step 6: Run final repository guards**

```bash
node scripts/check_frontend_boundaries.mjs
git diff --check
git status --short
```

- [ ] **Step 7: Update records and close the task**

Move `TASK-20260720-002` to completed in the progress ledger, set the current-task file to no active task, and record exact changed modules, commands/results, database/API/config impact, residual issues, and next step.

- [ ] **Step 8: Commit completion records**

```bash
git add docs/当前任务.md docs/开发进度与变更记录.md apps/web/tests/e2e
git commit -m "test(web): verify precision motion experience"
```

---

## Self-Review Result

- Spec coverage: landing/login, shell, metric C direction, list/action hierarchy, Dropdown/Dialog/Drawer, Tooltip/Hover/Artifact boundary, alerts, copy cleanup, responsive themes, keyboard, Reduced Motion, and verification each map to a task.
- Placeholder scan: no deferred implementation markers or undefined code placeholders remain.
- Type consistency: shared components consistently use `tone`, `state`, `loading`, `disabled`, `change`, and `action`; Feature migrations consume those same props.
- Scope consistency: no backend, database, OpenAPI, generated client, permission, pagination, or business-rule edits are planned.
