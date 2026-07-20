# Chromatic Signal Sidebar Icons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace monochrome workspace navigation icons with the approved compact chromatic-signal system while preserving routes, permissions, sidebar density, mobile navigation, and collapsed tooltips.

**Architecture:** Keep `projectNavigation` as the single navigation model and continue using Lucide for semantic geometry. Add one layout-owned icon renderer and a typed tone field, then let semantic CSS tokens own all color, active-state, and motion behavior; no Feature, API, or dependency changes are required.

**Tech Stack:** Next.js 16, React 19, TypeScript 6 strict, Lucide React, Tailwind CSS 4, Vitest/Testing Library, Playwright.

---

### Task 1: Lock the chromatic navigation contract

**Files:**
- Modify: `apps/web/src/components/layout/app-shell.test.tsx`
- Modify: `apps/web/src/styles/tokens.test.ts`

- [x] **Step 1: Replace the monochrome assertion with the desired icon contract**

Assert that the “测试用例” link exposes `data-navigation-tone="indigo"`, contains a `data-navigation-icon="chromatic-signal"` wrapper, one Lucide SVG, and a decorative `data-navigation-signal` element. Assert that all rendered navigation links have one of the five supported tones.

- [x] **Step 2: Add semantic Token and CSS behavior assertions**

Require `--navigation-coral`, `--navigation-blue`, `--navigation-mint`, `--navigation-amber`, and `--navigation-indigo` in both light and dark token blocks. Require active rows to use `--navigation-tone`, and Reduced Motion to disable `.app-nav-icon` transforms.

- [x] **Step 3: Run RED**

```bash
pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx src/styles/tokens.test.ts
```

Expected: FAIL because the current icon contract is `monochrome`, navigation items have no tone, and the new semantic tokens/CSS hooks do not exist.

### Task 2: Implement the typed icon system

**Files:**
- Create: `apps/web/src/components/layout/sidebar-navigation-icon.tsx`
- Modify: `apps/web/src/components/layout/app-shell-navigation.tsx`
- Modify: `apps/web/src/components/layout/app-shell.tsx`

- [x] **Step 1: Add the focused renderer**

Create a `NavigationTone` union for `coral | blue | mint | amber | indigo`. `SidebarNavigationIcon` accepts a `LucideIcon`, renders the existing `app-nav-icon` carrier, places the Lucide SVG inside a `chromatic-signal` wrapper, and adds an `aria-hidden` signal span.

- [x] **Step 2: Assign stable tones in the canonical navigation model**

Add `tone: NavigationTone` to every `NavigationItem`. Use the mapping from the approved design specification for project links, system users, command palette items, and mobile navigation. Replace `Check` with `BadgeCheck` for “人工审核”.

- [x] **Step 3: Render the typed icon and expose the tone to CSS**

Set `data-navigation-tone={item.tone}` on each link and render:

```tsx
<SidebarNavigationIcon icon={item.icon} tone={item.tone} />
```

Keep the existing collapsed shared `Tooltip`, `aria-label`, `aria-current`, exact route matching, and permission checks unchanged.

- [x] **Step 4: Run the focused test**

```bash
pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx
```

Expected: icon structure and navigation mapping assertions PASS; Token/CSS assertions remain RED until Task 3.

### Task 3: Add theme-aware color and restrained motion

**Files:**
- Modify: `apps/web/src/styles/tokens.css`
- Modify: `apps/web/src/app/globals.css`

- [x] **Step 1: Define light and dark semantic icon tones**

Add the five `--navigation-*` tokens beside the existing product/status colors in both theme blocks. Values must be contrast-tuned per theme and consumed only through semantic variables.

- [x] **Step 2: Implement the signal-line visual states**

Map each `data-navigation-tone` to `--navigation-tone`. Keep the carrier unframed, color the glyph with that variable, draw a short neutral diagonal signal, reduce inactive opacity, and use the same tone for the active rail and a low-opacity mixed active background.

- [x] **Step 3: Implement interaction and Reduced Motion**

On Hover/Focus apply `translateX(1px) scale(1.04)` to the glyph and a small signal-line shift using `--motion-fast`. Under `prefers-reduced-motion: reduce`, set the icon/signal transition to `none` and transform to `none`.

- [x] **Step 4: Run GREEN**

```bash
pnpm --filter @warmy/web exec vitest run src/components/layout/app-shell.test.tsx src/styles/tokens.test.ts
```

Expected: PASS with the chromatic structure, semantic tokens, active state, Tooltip, and Reduced Motion contracts.

### Task 4: Verify real shell behavior and visual quality

**Files:**
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`

- [x] **Step 1: Add a critical navigation E2E assertion**

In the authenticated desktop shell, assert the active navigation link has `aria-current="page"`, `data-navigation-tone`, and a visible chromatic icon. Collapse the sidebar, Hover/focus “测试用例”, assert its right-side Tooltip text, then expand it again. Reuse the existing route mocks and do not add test-only production branches.

- [x] **Step 2: Run the critical Playwright scenario**

```bash
E2E_API_PORT=8300 E2E_WEB_PORT=5293 pnpm --filter @warmy/web exec playwright test tests/e2e/list-layout.spec.ts --grep "chromatic sidebar" --workers=1
```

Expected: PASS at 1440px with no overlap or horizontal overflow.

- [x] **Step 3: Inspect four visual states**

Capture and inspect 1440px light/dark screenshots in expanded and collapsed states. Confirm icon alignment, color balance, active rail, Tooltip placement, no clipping, and no visible colored carrier box. Check the 390px mobile drawer once in each theme.

### Task 5: Full verification and handoff

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: `docs/superpowers/plans/2026-07-20-chromatic-signal-sidebar-icons.md`

- [x] **Step 1: Run frontend gates**

```bash
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
git diff --check
```

Expected: all commands PASS with no warnings introduced by this task.

- [x] **Step 2: Review boundaries and diff**

Confirm there are no route, permission, API, schema, generated-client, dependency, or business behavior changes; scan for copied external SVG content and raw colors outside `tokens.css`.

- [x] **Step 3: Complete repository records**

Move `TASK-20260720-007` to completed with exact commands and results, set `docs/当前任务.md` back to no active task, and mark each completed plan checkbox only after its evidence exists.

## Self-review

- Spec coverage: typed five-tone mapping, local signal layer, active rail, collapsed Tooltip, mobile reuse, dark theme and Reduced Motion each map to Tasks 1-4.
- Placeholder scan: no TODO/TBD or undefined implementation step remains.
- Type consistency: `NavigationTone`, `NavigationItem.tone`, `data-navigation-tone`, `chromatic-signal`, and `data-navigation-signal` use the same names throughout the plan.
