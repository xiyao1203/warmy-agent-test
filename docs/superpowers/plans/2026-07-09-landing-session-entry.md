# Landing Session Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the logged-in landing page experience so returning from the workbench to `/login` shows a Workbench button and enters the workspace without reopening login.

**Architecture:** `LoginScreen` will query the existing session with `getCurrentUser` and load projects only when the session exists. Login destination resolution moves into a small auth helper shared by `LoginForm` and `LoginScreen`, so popup-login and existing-session entry use identical routing rules.

**Tech Stack:** Next.js App Router, React, TanStack Query, TypeScript, Vitest, Testing Library.

---

### Task 1: Current Session Landing Test

**Files:**

- Modify: `apps/web/src/features/auth/tests/login-screen.test.tsx`
- Modify: `apps/web/src/features/auth/login-screen.tsx`

- [x] **Step 1: Write the failing test**

Add a test where `getCurrentUser` resolves and `listProjects` resolves to one active project. It must assert the top-right button says `工作台`, no login dialog opens, and clicking routes to `/projects/project-1/test-agent`.

- [x] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx`

Expected: FAIL because `LoginScreen` does not call `getCurrentUser` and the header still renders `登录`.

- [x] **Step 3: Implement minimal behavior**

Use `useQuery` in `LoginScreen`:

```tsx
const sessionQuery = useQuery({
  queryFn: getCurrentUser,
  queryKey: ["session"],
  retry: false,
});
const projectsQuery = useQuery({
  enabled: sessionQuery.isSuccess,
  queryFn: listProjects,
  queryKey: ["projects"],
  retry: false,
});
```

Render `工作台` when `workspaceEntryPath` exists or `sessionQuery.isSuccess`, and route via the resolved entry path instead of opening login.

- [x] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx`

Expected: PASS.

### Task 2: Shared Destination Helper

**Files:**

- Create: `apps/web/src/features/auth/login-destination.ts`
- Modify: `apps/web/src/features/auth/login-form.tsx`
- Test: `apps/web/src/features/auth/tests/login-form.test.tsx`

- [x] **Step 1: Extract destination logic**

Move default login destination, project-scoped returnTo detection, project selection and async list handling into `login-destination.ts`.

- [x] **Step 2: Keep existing login form tests green**

Run: `pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-form.test.tsx`

Expected: PASS, because the behavior remains unchanged.

### Task 3: Verify And Record

**Files:**

- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] **Step 1: Run targeted checks**

Run: `pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx src/features/auth/tests/login-form.test.tsx`

Expected: PASS.

- [x] **Step 2: Run quality gates**

Run:

```bash
pnpm --filter @warmy/web exec eslint src/features/auth/login-screen.tsx src/features/auth/login-form.tsx src/features/auth/login-destination.ts src/features/auth/tests/login-screen.test.tsx src/features/auth/tests/login-form.test.tsx
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web build
pnpm --filter @warmy/web test
git diff --check
```

Expected: PASS, with only known jsdom media warnings if full Vitest emits them.

- [x] **Step 3: Update task records**

Move `TASK-20260709-001` to completed in `docs/开发进度与变更记录.md`, set `docs/当前任务.md` back to no active task, and include exact verification evidence.
