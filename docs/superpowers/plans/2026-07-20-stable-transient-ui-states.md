# Stable Transient UI States Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent pointer-clicked tooltips from lingering and keep landing-page entry copy stable while the initial session request is pending.

**Architecture:** Fix Tooltip visibility once in the shared primitive by separating pointer hover from keyboard `:focus-visible`. Keep authentication data flow unchanged; only derive stable landing-page copy from confirmed authentication and expose pending state through disabled/ARIA state instead of temporary text.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS, CSS `:has()`, TanStack Query, Vitest, Testing Library, Playwright.

---

### Task 1: Fix shared Tooltip focus semantics

**Files:**
- Modify: `apps/web/src/components/uiverse/feedback/tooltip.tsx`
- Modify: `apps/web/src/components/ui/truncated-text.test.tsx`
- Modify: `apps/web/src/styles/tokens.test.ts`
- Modify: `apps/web/src/app/globals.css`

- [ ] **Step 1: Write failing component and CSS contract tests**

Require stable Tooltip hook classes, remove the broad focus-within utility, and require a CSS selector that only reveals on visible keyboard focus.

```tsx
expect(trigger.parentElement).toHaveClass("app-tooltip-trigger");
expect(screen.getByRole("tooltip")).toHaveClass("app-tooltip-content");
expect(screen.getByRole("tooltip")).not.toHaveClass(
  "group-focus-within:opacity-100",
);
```

```ts
expect(globalStyles).toContain(
  ".app-tooltip-trigger:has(:focus-visible) > .app-tooltip-content",
);
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/truncated-text.test.tsx src/styles/tokens.test.ts
```

Expected: FAIL because the shared Tooltip still uses only `group` and `group-focus-within` classes and the global selector does not exist.

- [ ] **Step 3: Implement visible-focus Tooltip styling**

Add `app-tooltip-trigger` to the wrapper and `app-tooltip-content` to the floating label. Keep `group-hover:opacity-100`, but remove `group-focus-within:opacity-100`.

```tsx
<div
  className={`app-tooltip-trigger group relative inline-flex min-w-0 max-w-full ${className}`}
>
  {children}
  <div
    className={`app-tooltip-content pointer-events-none absolute z-50 max-w-[min(18rem,calc(100vw-1rem))] ${whitespaceClass} rounded-[var(--radius-sm)] border border-[var(--hairline)] bg-[var(--surface-raised)] px-2 py-1 text-xs leading-4 text-[var(--ink)] opacity-0 shadow-[var(--shadow-overlay)] transition-[opacity,transform] duration-[var(--motion-fast)] after:content-[attr(data-tooltip)] group-hover:opacity-100 max-sm:hidden ${positionClasses[side]}`}
    data-tooltip={stringContent}
    role="tooltip"
  >
    {stringContent ? null : content}
  </div>
</div>
```

Add the keyboard-only rule near shared icon-button styles:

```css
.app-tooltip-trigger:has(:focus-visible) > .app-tooltip-content {
  opacity: 1;
}
```

- [ ] **Step 4: Verify GREEN**

Run the focused Vitest command and expect all tests to pass.

### Task 2: Stabilize landing-page session-check copy

**Files:**
- Modify: `apps/web/src/features/auth/tests/login-screen.test.tsx`
- Modify: `apps/web/src/features/auth/login-screen.tsx`

- [ ] **Step 1: Replace the pending-state test with the desired stable contract**

```tsx
it("keeps entry copy stable while the session check is pending", () => {
  getCurrentUserMock.mockReturnValue(new Promise(() => undefined));
  renderWithQueryClient(<LoginScreen />);

  expect(screen.queryByText("正在检查")).not.toBeInTheDocument();
  const headerEntry = screen.getByRole("button", { name: "登录" });
  const heroEntry = screen.getByRole("button", { name: "登录并开始" });
  for (const button of [headerEntry, heroEntry]) {
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  }
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/features/auth/tests/login-screen.test.tsx
```

Expected: FAIL because both buttons are still named `正在检查`.

- [ ] **Step 3: Implement stable copy and ARIA busy state**

Derive labels only from confirmed authentication:

```tsx
const headerEntryLabel = authenticated ? "工作台" : "登录";
const heroEntryLabel = authenticated ? "进入工作台" : "登录并开始";
```

For both buttons, add `aria-busy={entryResolving}`. Add `min-w-20` to the compact header entry button so `登录` and `工作台` do not shift neighboring controls. Keep `disabled={entryResolving}` and all routing behavior unchanged.

- [ ] **Step 4: Verify GREEN**

Run the focused login-screen test and expect all tests to pass.

### Task 3: Prove browser behavior and audit sibling states

**Files:**
- Modify: `apps/web/tests/e2e/login.spec.ts`
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`

- [ ] **Step 1: Add delayed-session landing coverage**

Intercept `/api/v1/auth/me` without immediately fulfilling it, navigate to `/login`, and assert there is no “正在检查”; the “登录 / 登录并开始” buttons remain disabled with `aria-busy="true"`. Release the delayed request with a 401 and assert both labels remain unchanged and become enabled.

- [ ] **Step 2: Extend the theme Tooltip browser contract**

After clicking the theme button, move the pointer away and wait for the motion duration. Require Tooltip opacity `0` while the button remains focused. Then press `Tab` followed by `Shift+Tab` and require Tooltip opacity `1`, proving keyboard focus still reveals it.

- [ ] **Step 3: Run critical Playwright**

Run:

```bash
E2E_API_PORT=8295 E2E_WEB_PORT=5288 pnpm --filter @warmy/web exec playwright test tests/e2e/login.spec.ts tests/e2e/list-layout.spec.ts --grep "pending|two-state|theme hydration" --workers=1
```

Expected: the pending-session scenario and two theme scenarios pass.

- [ ] **Step 4: Audit the repository for sibling startup labels**

Run searches for `正在检查`, conditional `isPending/isLoading` button labels, and shared Tooltip focus utilities. Classify explicit post-submit states as valid and ensure no other startup button exposes internal query status.

### Task 4: Verify and record completion

**Files:**
- Modify: `docs/superpowers/plans/2026-07-20-stable-transient-ui-states.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Run complete Web gates**

Run format, lint, typecheck, all Vitest, critical Playwright, production build, and `git diff --check`. Every command must exit 0.

- [ ] **Step 2: Capture and inspect the pending landing state**

Capture the 1440px header and Hero while the auth request is delayed. Confirm stable copy, no horizontal movement, no overlap, and no visible “正在检查”.

- [ ] **Step 3: Update task records**

Mark plan steps complete, move `TASK-20260720-006` to completed, record exact commands/results and the sibling-state audit, then restore no active task.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/uiverse/feedback/tooltip.tsx
git add apps/web/src/components/ui/truncated-text.test.tsx apps/web/src/styles/tokens.test.ts
git add apps/web/src/app/globals.css apps/web/src/features/auth/login-screen.tsx
git add apps/web/src/features/auth/tests/login-screen.test.tsx
git add apps/web/tests/e2e/login.spec.ts apps/web/tests/e2e/list-layout.spec.ts
git add docs/superpowers/plans/2026-07-20-stable-transient-ui-states.md
git add docs/当前任务.md docs/开发进度与变更记录.md
git commit -m "fix(web): stabilize transient ui states"
```
