# Direct Theme Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the two-item theme dropdown with one icon button that immediately toggles between explicit light and dark themes.

**Architecture:** Keep the existing `useSyncExternalStore` theme persistence and migration runtime intact. Simplify only the shared `ThemeToggle` presentation from a Radix menu to a native button wrapped by the platform Tooltip, then update its focused component and Playwright contracts.

**Tech Stack:** Next.js 16, React 19, TypeScript, Lucide React, platform Tooltip, Vitest, Testing Library, Playwright.

---

### Task 1: Lock the direct-click component contract

**Files:**
- Modify: `apps/web/src/components/layout/theme-toggle.test.tsx`
- Modify: `apps/web/src/components/layout/theme-toggle.tsx`

- [x] **Step 1: Replace the menu test with a failing direct-toggle test**

Set `localStorage.theme` to `light`, render `ThemeToggle`, and require one button named `切换至深色`. Assert its Sun icon and Tooltip, click once, then require `dark`, a Moon icon, the new name `切换至浅色`, and no `menu` or `menuitemradio` roles.

```tsx
it("toggles immediately without opening a theme menu", async () => {
  localStorage.setItem("theme", "light");
  render(<ThemeToggle />);

  const lightButton = screen.getByRole("button", { name: "切换至深色" });
  expect(lightButton.querySelector(".lucide-sun")).toBeInTheDocument();
  expect(screen.getByRole("tooltip")).toHaveAttribute(
    "data-tooltip",
    "切换至深色",
  );

  fireEvent.click(lightButton);

  await waitFor(() => expect(localStorage.getItem("theme")).toBe("dark"));
  const darkButton = screen.getByRole("button", { name: "切换至浅色" });
  expect(darkButton.querySelector(".lucide-moon")).toBeInTheDocument();
  expect(document.documentElement).toHaveClass("dark");
  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  expect(screen.queryByRole("menuitemradio")).not.toBeInTheDocument();
});
```

- [x] **Step 2: Run the focused test and verify RED**

Run:

```bash
pnpm --filter @warmy/web exec vitest run src/components/layout/theme-toggle.test.tsx
```

Expected: FAIL because the existing button is named `外观设置` and opens a menu instead of toggling directly.

- [x] **Step 3: Implement the minimal direct-toggle button**

Remove Radix Dropdown, `Check`, the option list, and `useMemo`. Import the shared Tooltip and derive the current icon, next theme, and action label directly.

```tsx
import { Moon, Sun } from "lucide-react";
import { useEffect, useSyncExternalStore } from "react";

import { Tooltip } from "@/components/uiverse";

const nextPreference: ThemePreference =
  preference === "light" ? "dark" : "light";
const actionLabel =
  nextPreference === "dark" ? "切换至深色" : "切换至浅色";
const ActiveIcon = preference === "dark" ? Moon : Sun;

return (
  <Tooltip content={actionLabel} side="bottom">
    <button
      aria-label={actionLabel}
      className={`app-icon-button ${className}`}
      onClick={() => selectTheme(nextPreference)}
      type="button"
    >
      <ActiveIcon
        aria-hidden="true"
        className="size-4"
        key={preference}
      />
    </button>
  </Tooltip>
);
```

Keep `getStoredPreference`, `subscribeToPreference`, `applyThemePreference`, the migration effect, and `selectTheme` behavior unchanged.

- [x] **Step 4: Run the focused test and verify GREEN**

Run the same focused Vitest command. Expected: both direct-toggle and legacy migration tests pass.

### Task 2: Add restrained icon feedback

**Files:**
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/src/components/layout/theme-toggle.test.tsx`

- [x] **Step 1: Add a focused style assertion**

Assert the rendered icon has the stable `theme-toggle-icon` class so the animation contract cannot silently disappear.

```tsx
expect(lightButton.querySelector(".theme-toggle-icon")).toBeInTheDocument();
```

- [x] **Step 2: Verify RED before adding the style hook**

Run the focused component test and expect failure because the current icon has no `theme-toggle-icon` class.

- [x] **Step 3: Add the style hook and token-based icon entry animation**

Change the icon class to `theme-toggle-icon size-4`, then add next to `.app-icon-button`:

```css
@keyframes theme-toggle-icon-enter {
  from {
    opacity: 0;
    transform: rotate(-18deg) scale(0.72);
  }
  to {
    opacity: 1;
    transform: rotate(0) scale(1);
  }
}

.theme-toggle-icon {
  animation: theme-toggle-icon-enter var(--motion-fast) ease-out both;
  transform-origin: center;
}
```

Add `.theme-toggle-icon` to the existing reduced-motion block that disables animation.

- [x] **Step 4: Verify component tests remain GREEN**

Run the focused component test and expect all tests to pass.

### Task 3: Replace the menu-based browser journey

**Files:**
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`

- [x] **Step 1: Rewrite the workbench theme assertions**

Replace menu clicks with the direct action button:

```ts
const darkToggle = page.getByRole("button", { name: "切换至深色" });
await darkToggle.hover();
await expect(page.getByRole("tooltip")).toHaveAttribute(
  "data-tooltip",
  "切换至深色",
);
await darkToggle.click();
await expect(page.locator("html")).toHaveClass(/dark/);
await expect(page.getByRole("menuitemradio")).toHaveCount(0);

await page.getByRole("button", { name: "切换至浅色" }).click();
await expect(page.locator("html")).toHaveClass(/light/);
```

Keep the existing dark-workspace screenshot and remove the obsolete theme-menu screenshot.

- [x] **Step 2: Run critical Playwright**

Run:

```bash
E2E_API_PORT=8293 E2E_WEB_PORT=5286 pnpm --filter @warmy/web exec playwright test tests/e2e/list-layout.spec.ts --grep "two-state|theme hydration" --workers=1
```

Expected: 2 passed, with no menu interaction and no Hydration errors.

### Task 4: Verify and record completion

**Files:**
- Modify: `docs/superpowers/plans/2026-07-20-direct-theme-toggle.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [x] **Step 1: Run complete Web gates**

Run format, lint, typecheck, all Vitest, critical Playwright, production build, and `git diff --check`. Every command must exit 0.

- [x] **Step 2: Perform visual verification**

Capture the header in light and dark states at 1440px. Verify that one click changes theme, no menu appears, the current icon changes, the Tooltip names the target action, and controls do not shift or overlap.

- [x] **Step 3: Update task records**

Mark every plan checkbox complete, move `TASK-20260720-005` from current to completed, record exact files and command results, and restore `docs/当前任务.md` to no active task.

- [x] **Step 4: Commit the implementation**

```bash
git add apps/web/src/components/layout/theme-toggle.tsx \
  apps/web/src/components/layout/theme-toggle.test.tsx \
  apps/web/src/app/globals.css \
  apps/web/tests/e2e/list-layout.spec.ts \
  docs/superpowers/plans/2026-07-20-direct-theme-toggle.md \
  docs/当前任务.md \
  docs/开发进度与变更记录.md
git commit -m "feat(web): toggle theme directly"
```
