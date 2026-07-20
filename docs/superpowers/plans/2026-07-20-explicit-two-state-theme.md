# Explicit Two-State Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the light/dark/system theme preference with an explicit light/dark choice while safely migrating legacy system preferences.

**Architecture:** Keep the root bootstrap script responsible for pre-hydration theme selection and migration. Keep `ThemeToggle` as the shared runtime controller, but remove media-query subscriptions; account preferences consume only the two explicit choices while the backend contract remains unchanged.

**Tech Stack:** Next.js 16, React 19, TypeScript, Radix Dropdown Menu, Vitest, Testing Library, Playwright.

---

### Task 1: Lock the two-state runtime contract

**Files:**
- Modify: `apps/web/src/components/layout/theme-toggle.test.tsx`

- [ ] **Step 1: Write failing tests**

Require exactly two menu radio items, assert “跟随系统” is absent, and verify a stored `system` value resolves to the current media theme, is persisted as `light` or `dark`, and does not register a media change listener.

- [ ] **Step 2: Verify RED**

Run: `pnpm --filter @warmy/web exec vitest run src/components/layout/theme-toggle.test.tsx`

Expected: FAIL because the third option and media listener still exist.

- [ ] **Step 3: Implement the minimal runtime change**

Modify `apps/web/src/components/layout/theme-toggle.tsx`: use `ThemePreference = "light" | "dark"`, remove Laptop and system subscriptions, resolve invalid/legacy storage once through `matchMedia`, then persist and apply the explicit result.

- [ ] **Step 4: Verify GREEN**

Run the focused component test and expect all tests to pass.

### Task 2: Update pre-hydration and account preferences

**Files:**
- Modify: `apps/web/src/app/layout.tsx`
- Modify: `apps/web/src/features/account/preferences-section.tsx`
- Modify: `apps/web/src/features/account/tests/account-settings.test.tsx`

- [ ] **Step 1: Write the failing account test**

Assert the account section renders only “浅色”和“深色” and never renders “跟随系统”.

- [ ] **Step 2: Verify RED**

Run the account settings test and expect failure on the third theme option.

- [ ] **Step 3: Implement bootstrap migration and two account choices**

Remove the pre-hydration media listener, migrate missing/invalid/`system` local storage to the current resolved mode, and reduce account theme cards to a two-column `light | dark` set. Map a legacy server `system` value to the root element’s resolved theme.

- [ ] **Step 4: Verify GREEN and typecheck**

Run both component test files and `pnpm --filter @warmy/web typecheck`.

### Task 3: Replace three-state E2E coverage

**Files:**
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`

- [ ] **Step 1: Update browser assertions**

Rename the theme scenarios for two-state behavior, assert the system menu item is absent, verify light/dark switching, and verify a legacy stored `system` migrates once and ignores later emulated system changes.

- [ ] **Step 2: Run critical Playwright**

Run: `E2E_API_PORT=8291 E2E_WEB_PORT=5284 pnpm --filter @warmy/web exec playwright test tests/e2e/list-layout.spec.ts --grep "theme|two-state" --workers=1`

Expected: both theme scenarios pass without hydration errors.

### Task 4: Synchronize design contract and finish

**Files:**
- Modify: `docs/design.md`
- Modify: `docs/superpowers/specs/2026-07-20-precision-motion-platform-ui-design.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Update design documentation**

Replace three-state wording with explicit light/dark behavior and document the one-time legacy migration.

- [ ] **Step 2: Run complete Web gates**

Run format, lint, typecheck, all Vitest, critical Playwright, and production build. All must exit 0.

- [ ] **Step 3: Record completion and commit**

Move `TASK-20260720-004` to completed, restore no active task, and commit the focused change on the current development branch.
