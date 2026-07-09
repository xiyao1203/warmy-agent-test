# Workbench Brand Landing Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the logged-in workbench brand return to the landing page and keep users on the landing page after login until they click an entry button.

**Architecture:** Keep navigation responsibility at the existing UI boundary. `AppShell` owns the logged-in header brand link, while `LoginScreen` owns the landing dialog flow and stores the resolved workspace path after successful authentication.

**Tech Stack:** Next.js App Router, React, TypeScript, Vitest, Testing Library.

---

### Task 1: Lock Workbench Brand Behavior

**Files:**
- Modify: `apps/web/src/components/layout/app-shell.test.tsx`
- Modify: `apps/web/src/components/layout/app-shell.tsx`

- [x] **Step 1: Write the failing test**

Update the `AppShell` ordinary-user test and 3D brand test so the global brand is addressed as `Warmy Agent Test` and links to `/login`.

```tsx
expect(screen.getByText("Warmy Agent Test")).toBeInTheDocument();
expect(
  screen.getByRole("link", { name: "Warmy Agent Test" }),
).toHaveAttribute("href", "/login");
```

- [x] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx`

Expected: FAIL because the current header still exposes `Agent Test` and links to `/projects/project-1/test-agent`.

- [x] **Step 3: Write minimal implementation**

Change the `AppShell` header brand link:

```tsx
<Link
  aria-label="Warmy Agent Test"
  className="font-display flex shrink-0 items-center gap-2 text-base font-semibold"
  href="/login"
>
  <BrandMark compact={collapsed} />
  {!collapsed && <span>Warmy Agent Test</span>}
</Link>
```

- [x] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx`

Expected: PASS.

### Task 2: Lock Landing Login Entry Behavior

**Files:**
- Modify: `apps/web/src/features/auth/tests/login-screen.test.tsx`
- Modify: `apps/web/src/features/auth/login-screen.tsx`

- [x] **Step 1: Write the failing test**

Mock login and project loading. Submit the login dialog, assert no immediate router navigation, then click `进入工作台` and assert it navigates to `/projects/project-1/test-agent`.

```tsx
expect(router.replace).not.toHaveBeenCalled();
expect(router.push).not.toHaveBeenCalled();
fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));
expect(router.push).toHaveBeenCalledWith("/projects/project-1/test-agent");
```

- [x] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx`

Expected: FAIL because `handleSuccess` currently calls `router.replace(path)` immediately.

- [x] **Step 3: Write minimal implementation**

Store the resolved workspace path after login and route only from the entry buttons:

```tsx
const [workspaceEntryPath, setWorkspaceEntryPath] = useState<string | null>(
  null,
);

function handleSuccess(path: string) {
  setWorkspaceEntryPath(path);
  setLoginOpen(false);
}

function openWorkspaceEntry() {
  if (workspaceEntryPath) {
    router.push(workspaceEntryPath);
    return;
  }
  setLoginOpen(true);
}
```

- [x] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx`

Expected: PASS.

### Task 3: Lock Browser Title Brand

**Files:**
- Create: `apps/web/src/app/tests/layout-metadata.test.ts`
- Modify: `apps/web/src/app/layout.tsx`

- [x] **Step 1: Write the failing test**

```ts
import { metadata } from "../layout";

it("uses the Warmy Agent Test product name in metadata", () => {
  expect(metadata.title).toBe("Warmy Agent Test");
});
```

- [x] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @warmy/web exec vitest run src/app/tests/layout-metadata.test.ts`

Expected: FAIL because `metadata.title` is currently `Agent Test`.

- [x] **Step 3: Write minimal implementation**

Change the metadata title:

```ts
export const metadata: Metadata = {
  title: "Warmy Agent Test",
  description: "Agent automation testing and security evaluation platform",
};
```

- [x] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @warmy/web exec vitest run src/app/tests/layout-metadata.test.ts`

Expected: PASS.

### Task 4: Verify And Record

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] **Step 1: Run targeted tests**

Run: `pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx src/features/auth/tests/login-screen.test.tsx src/app/tests/layout-metadata.test.ts`

Expected: PASS.

- [x] **Step 2: Run quality gates**

Run:

```bash
pnpm --filter @warmy/web exec eslint src/components/layout/app-shell.tsx src/components/layout/app-shell.test.tsx src/features/auth/login-screen.tsx src/features/auth/tests/login-screen.test.tsx src/app/layout.tsx src/app/tests/layout-metadata.test.ts
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web build
pnpm --filter @warmy/web test
git diff --check
```

Expected: PASS, with only known jsdom media warnings if the full suite emits them.

- [x] **Step 3: Update records**

Move `TASK-20260708-006` to completed in `docs/开发进度与变更记录.md`, set `docs/当前任务.md` back to no active task, and include exact verification commands.
