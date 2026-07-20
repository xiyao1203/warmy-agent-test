# Pagination Footer Right Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move page-size selection into the right-aligned pagination control group across all resource lists without changing pagination behavior.

**Architecture:** Keep `ResourcePagination` as the single shared owner. Split its footer into a left total label and a right flex container that owns the Select, page summary, and Pagination navigation; use responsive wrapping inside that right container.

**Tech Stack:** React 19, TypeScript, Tailwind CSS utilities, Vitest, Testing Library, Playwright.

---

### Task 1: Lock the shared footer contract

**Files:**
- Modify: `apps/web/src/components/ui/resource-pagination.test.tsx`

- [x] **Step 1: Write the failing test**

Add assertions that `共 42 条` belongs to `data-pagination-total`, while the `每页条数` combobox, `第 2 / 5 页`, and pagination navigation all belong to `data-pagination-controls`.

- [x] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @warmy/web exec vitest run src/components/ui/resource-pagination.test.tsx`

Expected: FAIL because the two layout groups do not exist and the Select is still grouped with the total.

### Task 2: Implement the right-aligned control group

**Files:**
- Modify: `apps/web/src/components/ui/resource-pagination.tsx`

- [x] **Step 1: Write minimal implementation**

Render the total as `data-pagination-total` and wrap the Select, page summary, and Pagination in `className="ml-auto flex flex-wrap items-center justify-end gap-3"` with `data-pagination-controls`.

- [x] **Step 2: Run focused tests**

Run: `pnpm --filter @warmy/web exec vitest run src/components/ui/resource-pagination.test.tsx src/lib/pagination.test.ts src/lib/use-pagination-state.test.tsx`

Expected: all tests PASS.

### Task 3: Verify responsive geometry

**Files:**
- Modify: `apps/web/tests/e2e/core-pagination.spec.ts`

- [x] **Step 1: Add geometry assertions**

Assert at desktop width that `data-pagination-controls` is to the right of `data-pagination-total` and aligned with the footer right edge. At 390px assert the controls do not exceed the viewport and retain `justify-content: flex-end`.

- [x] **Step 2: Run critical E2E**

Run: `E2E_API_PORT=8290 E2E_WEB_PORT=5283 pnpm --filter @warmy/web exec playwright test tests/e2e/core-pagination.spec.ts`

Expected: pagination test PASS with no horizontal overflow.

### Task 4: Complete quality gates and records

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] **Step 1: Run Web gates**

Run `format`, `lint`, `typecheck`, relevant Vitest, Playwright, and `build`; all commands must exit 0.

- [x] **Step 2: Update task records**

Move `TASK-20260720-003` to completed with exact verification evidence and restore `docs/当前任务.md` to no active task.

- [x] **Step 3: Commit**

Commit the focused implementation and documentation on `codex/pagination-footer-right-alignment`.
