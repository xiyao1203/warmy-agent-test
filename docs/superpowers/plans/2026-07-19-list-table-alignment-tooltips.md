# List Table Alignment And Action Tooltips Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make every resource list allocate columns from field content, center values beneath their headers, and expose a concise hover/focus name for every icon action.

**Architecture:** Extend the existing shared `Table` and `TableActionButton` primitives so layout and accessible action behavior have one owner. Feature lists declare only semantic minimum widths and rich-value wrappers; a source-level contract test prevents fixed percentage layouts and unlabelled icon actions from returning.

**Tech Stack:** Next.js 16, React 19, TypeScript Strict, Tailwind CSS, Radix Dialog, Vitest, Testing Library, Playwright.

---

### Task 1: Establish shared adaptive table and action contracts

**Files:**

- Modify: `apps/web/src/components/ui/table.tsx`
- Modify: `apps/web/src/components/ui/table.test.tsx`
- Modify: `apps/web/src/components/ui/table-actions.tsx`
- Modify: `apps/web/src/components/ui/table-actions.test.tsx`
- Create: `apps/web/src/test/architecture/list-table-contract.test.ts`

- [x] **Step 1: Add failing shared component tests**

Assert that `Table` uses `table-auto`, `TableHead` and `TableCell` use `text-center`, and the new `TableValue` centers a left-aligned rich content block. Assert `TableActionButton label="编辑" accessibleLabel="编辑项目 A"` renders Tooltip “编辑” and an accessible button name “编辑项目 A”.

- [x] **Step 2: Add a failing resource-list architecture test**

Scan the explicit resource-list manifest and fail on `table-fixed`, `w-[NN%]`, raw icon-only action buttons, or long resource interpolation in `TableActionButton.label`. The manifest covers projects, agents, datasets, dataset detail, test plans, runs, environments, browser profiles, model configs, test accounts, users and project overview.

- [x] **Step 3: Run the tests and confirm RED**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/table.test.tsx src/components/ui/table-actions.test.tsx src/test/architecture/list-table-contract.test.ts
```

Expected: failures show fixed layout, left-aligned defaults, missing `TableValue`, and the old single-name action API.

- [x] **Step 4: Implement the shared primitives**

Change the stable APIs to:

```tsx
export function TableValue({
  className = "",
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`mx-auto w-fit max-w-full text-left ${className}`}
      {...props}
    />
  );
}

type TableActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  accessibleLabel?: string;
  asChild?: boolean;
  children: ReactNode;
  label: string;
  tone?: "danger" | "default";
};
```

`label` owns only the concise Tooltip; `aria-label` uses `accessibleLabel ?? label`. Keep stable 32px icon dimensions, dangerous tone and `asChild` behavior.

- [x] **Step 5: Verify GREEN and commit**

Run the Task 1 command, then:

```bash
git add apps/web/src/components/ui apps/web/src/test/architecture/list-table-contract.test.ts
git commit -m "refactor(web): standardize adaptive list primitives"
```

### Task 2: Migrate every table-backed resource list

**Files:**

- Modify: `apps/web/src/features/projects/project-list-screen.tsx`
- Modify: `apps/web/src/features/projects/project-overview.tsx`
- Modify: `apps/web/src/features/agents/agent-list.tsx`
- Modify: `apps/web/src/features/datasets/dataset-list.tsx`
- Modify: `apps/web/src/features/datasets/dataset-detail.tsx`
- Modify: `apps/web/src/features/test-plans/test-plan-list.tsx`
- Modify: `apps/web/src/features/runs/run-center.tsx`
- Modify: `apps/web/src/features/environments/environment-list.tsx`
- Modify: `apps/web/src/features/browser-profiles/browser-profile-list.tsx`
- Modify: `apps/web/src/features/model-configs/model-config-list.tsx`
- Modify: `apps/web/src/features/test-accounts/test-account-list.tsx`
- Modify: `apps/web/src/features/users/user-management.tsx`
- Modify: associated existing `*.test.tsx` files

- [x] **Step 1: Convert fixed percentage columns to semantic columns**

Remove `table-fixed` and every percentage width. Use `min-w-*` for name/summary columns, `whitespace-nowrap` for status/date columns, and `tableActionHeadClass` for actions. Keep the existing mobile project-row transformation unchanged.

- [x] **Step 2: Align values beneath headers**

Use `TableValue` for all multi-line name, description, asset, execution and quality blocks. Short values remain directly centered. Do not center the text inside a multi-line block; center the block itself.

- [x] **Step 3: Normalize all table actions**

Use concise labels (`进入`, `编辑`, `归档`, `管理`, `删除`, `查看`, `校验`, `发布`, `启用`, `停用`) and resource-specific `accessibleLabel`. Wrap delete Dialog triggers in the shared Tooltip without changing confirmation behavior.

- [x] **Step 4: Run list component regressions**

Run:

```bash
pnpm --filter @warmy/web exec vitest run \
  src/features/projects/tests \
  src/features/agents/tests \
  src/features/datasets/tests \
  src/features/test-plans/tests \
  src/features/runs/tests \
  src/features/environments/tests \
  src/features/browser-profiles/tests \
  src/features/model-configs/tests \
  src/features/test-accounts \
  src/features/users
```

Expected: CRUD callbacks, links, confirmation dialogs, permission states and existing field content remain unchanged.

- [x] **Step 5: Run the architecture contract and commit**

```bash
pnpm --filter @warmy/web exec vitest run src/test/architecture/list-table-contract.test.ts
git add apps/web/src/features apps/web/src/test/architecture/list-table-contract.test.ts
git commit -m "refactor(web): align resource list columns"
```

### Task 3: Complete card-list tooltips and browser layout coverage

**Files:**

- Modify: `apps/web/src/features/scorers/scorer-list.tsx`
- Modify: `apps/web/src/features/gates/gate-list.tsx`
- Modify: `apps/web/src/features/test-agent/session-list.tsx`
- Modify: any remaining resource-list file reported by the architecture scan
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`

- [x] **Step 1: Add missing card/row action Tooltip tests**

Extend existing component tests to assert visible Tooltip data for delete/manage actions while preserving complete `aria-label` values.

- [x] **Step 2: Migrate remaining resource actions**

Wrap raw icon-only resource actions in `TableActionButton` or `Tooltip`. Do not change form-row editors, chat composer actions, Trace controls or full text command buttons.

- [x] **Step 3: Add multi-viewport Playwright assertions**

For project, Agent, dataset, test-plan and run tables at 1280, 1440 and 1920, compare the horizontal center of each visible header with its matching cell content block, allow a small rendering tolerance, and assert the action group stays one horizontal row. Hover the first action and assert its short Tooltip is visible and not vertically wrapped. Retain the existing 390px no-page-overflow assertion.

- [x] **Step 4: Run focused browser tests and commit**

```bash
pnpm --filter @warmy/web exec playwright test tests/e2e/list-layout.spec.ts
git add apps/web/src/features apps/web/tests/e2e/list-layout.spec.ts
git commit -m "test(web): cover adaptive list layouts"
```

### Task 4: Verify, document and finish the branch

**Files:**

- Modify: `apps/web/next-env.d.ts`
- Modify: `apps/web/tsconfig.json`
- Modify: `docs/design.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: this plan

- [x] **Step 1: Repair the tracked generated Next type reference**

Replace the accidentally committed machine-specific temporary paths in `next-env.d.ts` and `tsconfig.json` with repository-relative Next type references and prove no `/var/folders` path remains in tracked Web configuration.

- [x] **Step 2: Run all Web gates**

```bash
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
pnpm --filter @warmy/web run perf:bundle-check
pnpm --filter @warmy/web e2e
```

Expected: all Web tests and 4 bundle budgets pass; only the credential-conditioned performance scenario may skip.

- [x] **Step 3: Verify scope and implementation contracts**

```bash
git diff --check
rg -n 'table-fixed|w-\[[0-9]+%\]' apps/web/src/features/{projects,agents,datasets,test-plans,runs,environments,browser-profiles,model-configs,test-accounts,users}
rg -n '/var/folders|agenttest-e2e\.' apps/web/next-env.d.ts apps/web/tsconfig.json
git diff --exit-code -- docs/api/openapi.json packages/generated-api-client/src/client
```

Expected: both scans are empty and API/generated client files are unchanged.

- [x] **Step 4: Update design and task records**

Record actual files, exact Vitest/Playwright counts, viewport coverage, build and bundle results. Move `TASK-20260719-001` to completed and set `docs/当前任务.md` to no active task.

- [x] **Step 5: Final review and commit**

Review for broken Dialog triggers, lost accessible names, disabled/loading regressions, overflowing long values, mobile page overflow and unrelated product changes, then run the final focused tests again.

```bash
git add apps/web docs
git commit -m "refactor(web): complete adaptive resource lists"
```

Do not push or merge unless explicitly requested.
