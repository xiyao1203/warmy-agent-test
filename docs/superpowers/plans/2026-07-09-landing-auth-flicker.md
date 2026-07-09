# Landing Auth Flicker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent the landing page from showing "登录" while the existing session check is still pending.

**Architecture:** Keep the fix inside `LoginScreen`, where TanStack Query already owns the session state. Treat `sessionQuery.isPending` as an explicit unknown-auth state: show a disabled workbench entry until the session is resolved, then use the existing workbench/login behavior.

**Tech Stack:** Next.js App Router, React, TanStack Query, Vitest, Testing Library.

---

### Task 1: Reproduce Pending-Session Button Flicker

**Files:**

- Modify: `apps/web/src/features/auth/tests/login-screen.test.tsx`

- [x] **Step 1: Write the failing test**

Add a test that leaves `getCurrentUserMock` pending and asserts the landing header does not render the "登录" button during the pending session check:

```tsx
it("does not show login while the existing session check is still pending", () => {
  getCurrentUserMock.mockReturnValue(new Promise(() => undefined));

  renderWithQueryClient(<LoginScreen />);

  expect(
    screen.queryByRole("button", { name: "登录" }),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "工作台" })).toBeDisabled();
});
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx
```

Expected: FAIL because the current pending state renders the "登录" button.

### Task 2: Add Unknown-Session Entry State

**Files:**

- Modify: `apps/web/src/features/auth/login-screen.tsx`

- [x] **Step 1: Implement minimal state change**

Add a `sessionChecking` boolean from `sessionQuery.isPending`, include it in `hasWorkspaceEntry`, and keep the button disabled while the final entry path is unresolved:

```tsx
const sessionChecking = sessionQuery.isPending;
const hasWorkspaceEntry =
  sessionChecking || Boolean(workspaceEntryPath) || sessionQuery.isSuccess;
const entryResolving = hasWorkspaceEntry && !effectiveEntryPath;
```

- [x] **Step 2: Run focused tests**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx
```

Expected: PASS, including the new pending-session test.

### Task 3: Verify And Record

**Files:**

- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] **Step 1: Run verification**

Run:

```bash
pnpm --filter @warmy/web exec eslint src/features/auth/login-screen.tsx src/features/auth/tests/login-screen.test.tsx
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web build
git diff --check
```

Expected: all commands exit 0.

- [x] **Step 2: Update task records**

Move `TASK-20260709-003` from current/ongoing to completed and record the test and verification commands.
