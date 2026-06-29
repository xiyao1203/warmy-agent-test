# Help Center and Profile Structure Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the help and account surfaces around shared, compact page structures while preserving every existing real API interaction.

**Architecture:** Add a reusable Help Feature shell driven by one navigation model, then let route pages provide only their content. Keep the Account Feature as the owner of section normalization and profile mutation state; route pages remain thin composition boundaries. No backend, generated-client, or global-token changes are required.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript 6, Tailwind CSS 4, TanStack Query 5, Lucide React, Vitest, Testing Library.

---

## File map

- Create `apps/web/src/features/help/help-navigation.ts`: canonical help navigation and topic data.
- Create `apps/web/src/features/help/help-shell.tsx`: shared responsive help header, desktop sidebar, mobile navigation, and content frame.
- Modify `apps/web/src/features/help/help-search.tsx`: result count, clearer empty state, and feedback route.
- Modify `apps/web/src/features/help/index.ts`: public Help Feature exports.
- Modify `apps/web/src/app/(help)/layout.tsx`: wrap every help route in `HelpShell`.
- Modify all files under `apps/web/src/app/(help)/docs/**` and `feedback/page.tsx`: content-only pages using the shared frame.
- Create `apps/web/src/features/help/tests/help-shell.test.tsx`: navigation and current-page behavior.
- Modify `apps/web/src/features/help/tests/help-search.test.tsx`: result summary and empty-state actions.
- Create `apps/web/src/features/help/tests/help-pages.test.tsx`: static content and route integrity.
- Modify `apps/web/src/features/account/types.ts`: safe account-section normalization.
- Modify `apps/web/src/features/account/account-center.tsx`: compact hierarchy, valid selected state, and `aria-current`.
- Modify `apps/web/src/features/account/profile-section.tsx`: condensed identity summary, detail rows, status copy, retry state, and local edit form.
- Modify `apps/web/src/app/(account)/account/page.tsx`: normalized section composition and simplified shell header.
- Modify `apps/web/src/features/account/tests/account-center.test.tsx`: invalid-section fallback and accessibility state.
- Create `apps/web/src/features/account/tests/profile-section.test.tsx`: loading, display, edit, cancel, save, and error behavior.
- Modify `apps/web/src/features/account/preferences-section.tsx`, `notifications-section.tsx`, and `security-section.tsx`: align information density and remove unsupported destructive action.
- Update `docs/当前任务.md` and `docs/开发进度与变更记录.md`: implementation and verification evidence.

### Task 1: Shared help-center frame

**Files:**
- Create: `apps/web/src/features/help/help-navigation.ts`
- Create: `apps/web/src/features/help/help-shell.tsx`
- Create: `apps/web/src/features/help/tests/help-shell.test.tsx`
- Modify: `apps/web/src/features/help/index.ts`
- Modify: `apps/web/src/app/(help)/layout.tsx`

- [ ] **Step 1: Write the failing shell test**

Add a `next/navigation` mock returning `/docs/tutorials`, render `HelpShell`, and assert that the shared frame exposes the product return link, all six help destinations, the child content, and `aria-current="page"` on “教程”。

```tsx
it("marks the current help destination and renders shared actions", () => {
  render(<HelpShell><p>教程内容</p></HelpShell>);
  expect(screen.getByRole("link", { name: "返回应用" })).toHaveAttribute("href", "/projects");
  expect(screen.getByRole("link", { name: "教程" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("link", { name: "提交反馈" })).toHaveAttribute("href", "/feedback");
  expect(screen.getByText("教程内容")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests/help-shell.test.tsx`

Expected: FAIL because `HelpShell` and `help-navigation.ts` do not exist.

- [ ] **Step 3: Implement the canonical navigation and shell**

Define immutable navigation entries for `/docs`, `/docs#quickstart`, `/docs/test-cases`, `/docs/tutorials`, `/docs/shortcuts`, and `/feedback`. `HelpShell` must use `usePathname()`, mark exact or nested route matches, render a sticky 56-pixel header, a desktop 192-pixel sidebar, a horizontally scrollable mobile nav, and a `min-w-0` content column.

```ts
export const helpNavigation = [
  { href: "/docs", label: "帮助首页", icon: LifeBuoy },
  { href: "/docs#quickstart", label: "快速开始", icon: Rocket },
  { href: "/docs/test-cases", label: "测试用例", icon: ListChecks },
  { href: "/docs/tutorials", label: "教程", icon: GraduationCap },
  { href: "/docs/shortcuts", label: "快捷键", icon: Keyboard },
  { href: "/feedback", label: "反馈", icon: MessageSquare },
] as const;
```

- [ ] **Step 4: Export and install the shell at the route-group layout**

`features/help/index.ts` exports `HelpShell` and navigation types/data. `app/(help)/layout.tsx` returns `<HelpShell>{children}</HelpShell>` so child routes no longer own top bars.

- [ ] **Step 5: Run the focused test and verify GREEN**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests/help-shell.test.tsx`

Expected: PASS.

### Task 2: Help search and landing-page hierarchy

**Files:**
- Modify: `apps/web/src/features/help/help-search.tsx`
- Modify: `apps/web/src/features/help/tests/help-search.test.tsx`
- Modify: `apps/web/src/app/(help)/docs/page.tsx`

- [ ] **Step 1: Add failing search behavior tests**

Add assertions that an active query announces “找到 1 条结果”, the empty state links to `/feedback`, and the result list uses an accessible label.

```tsx
fireEvent.change(screen.getByRole("searchbox"), { target: { value: "Agent" } });
expect(screen.getByText("找到 1 条结果")).toBeInTheDocument();
expect(screen.getByRole("region", { name: "搜索结果" })).toBeInTheDocument();
```

- [ ] **Step 2: Run the search test and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests/help-search.test.tsx`

Expected: FAIL because the result announcement and region do not exist.

- [ ] **Step 3: Implement the search result summary and empty-state actions**

Use a normalized trimmed query, add an `aria-live="polite"` result summary only while searching, label the result region, and include both “清空搜索” and “提交反馈” actions when no result matches.

- [ ] **Step 4: Rebuild the help landing page as compact content**

Remove the duplicate top bar, gradient hero, per-card gradients, fake mail link, and dead anchors. Render: page heading; full-width `HelpSearch`; four real topic rows; a five-step `#quickstart` ordered path; accessible FAQ; and a final feedback callout linked to `/feedback`.

- [ ] **Step 5: Run help-search tests and verify GREEN**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests/help-search.test.tsx`

Expected: all help-search tests PASS.

### Task 3: Content-only help routes

**Files:**
- Create: `apps/web/src/features/help/tests/help-pages.test.tsx`
- Modify: `apps/web/src/app/(help)/docs/tutorials/page.tsx`
- Modify: `apps/web/src/app/(help)/docs/test-cases/page.tsx`
- Modify: `apps/web/src/app/(help)/docs/shortcuts/page.tsx`
- Modify: `apps/web/src/app/(help)/feedback/page.tsx`

- [ ] **Step 1: Write failing page-structure tests**

Render each synchronous page component and assert one level-one heading, no duplicated “返回应用” link inside the content, tutorial rows containing `aria-label`-free semantic text instead of emoji thumbnails, and the feedback page containing the real `FeedbackForm` fields.

```tsx
render(<TutorialsPage />);
expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
expect(screen.queryByRole("link", { name: "返回应用" })).not.toBeInTheDocument();
expect(screen.getByText("阅读指南")).toBeInTheDocument();
```

- [ ] **Step 2: Run the page test and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests/help-pages.test.tsx`

Expected: FAIL because each page still contains its own top bar and tutorials still use emoji thumbnails.

- [ ] **Step 3: Convert tutorials to a resource list**

Render six bordered rows with Lucide icons, title, description, estimated duration, and a truthful “阅读指南” content-type label. Do not render fake play controls or imply unavailable video playback.

- [ ] **Step 4: Convert the test-case and shortcut pages to article/table layouts**

Keep one page heading per route. Use numbered article sections and a single best-practice panel for test cases; use grouped `dl`/row structures with semantic `kbd` elements for shortcuts. Both pages must rely on the shared outer width and header.

- [ ] **Step 5: Simplify the feedback page**

Keep a compact title and explanatory copy above the existing `FeedbackForm`; remove its duplicate page header and fixed-width full-screen wrapper.

- [ ] **Step 6: Run the page and feedback tests and verify GREEN**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests/help-pages.test.tsx src/features/help/tests/feedback-form.test.tsx`

Expected: all selected tests PASS.

### Task 4: Safe, compact account navigation

**Files:**
- Modify: `apps/web/src/features/account/types.ts`
- Modify: `apps/web/src/features/account/account-center.tsx`
- Modify: `apps/web/src/features/account/tests/account-center.test.tsx`
- Modify: `apps/web/src/app/(account)/account/page.tsx`

- [ ] **Step 1: Add failing normalization and navigation-state tests**

Mock `useSearchParams()` with `section=unknown`, render `AccountCenter`, and assert “个人资料” owns `aria-current="page"`. Test `normalizeAccountSection("security") === "security"` and `normalizeAccountSection("unknown") === "profile"`.

- [ ] **Step 2: Run account-center tests and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/account-center.test.tsx`

Expected: FAIL because invalid values are cast and links lack `aria-current`.

- [ ] **Step 3: Implement section normalization**

```ts
export function normalizeAccountSection(value: string | null | undefined): AccountSection {
  return accountSections.some((section) => section.id === value)
    ? (value as AccountSection)
    : "profile";
}
```

Use it in both the client navigation and server route composition.

- [ ] **Step 4: Restyle the account frame**

Use a maximum width near 1040 pixels, semibold 24-pixel heading, subtle sidebar selection, `aria-current`, and a single content surface with `min-w-0`. Keep horizontal mobile navigation and remove the large solid-primary selection blocks.

- [ ] **Step 5: Run account-center tests and verify GREEN**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/account-center.test.tsx`

Expected: all account-center tests PASS.

### Task 5: Profile information and account-section polish

**Files:**
- Create: `apps/web/src/features/account/tests/profile-section.test.tsx`
- Modify: `apps/web/src/features/account/profile-section.tsx`
- Modify: `apps/web/src/features/account/preferences-section.tsx`
- Modify: `apps/web/src/features/account/notifications-section.tsx`
- Modify: `apps/web/src/features/account/security-section.tsx`

- [ ] **Step 1: Write failing profile tests**

Mock the account API and render with a fresh `QueryClient`. Assert the identity summary shows display name, email, translated role/status labels, and one “编辑资料” button. Enter edit mode, cancel, submit changed values, and verify API errors are associated with an alert.

```tsx
expect(await screen.findByText("测试用户")).toBeInTheDocument();
expect(screen.getByText("开发")).toBeInTheDocument();
expect(screen.getByText("正常")).toBeInTheDocument();
fireEvent.click(screen.getByRole("button", { name: "编辑资料" }));
expect(screen.getByLabelText("显示名称")).toHaveValue("测试用户");
```

- [ ] **Step 2: Run the profile test and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/profile-section.test.tsx`

Expected: FAIL because role/status translations, alert semantics, and compact field structure are absent.

- [ ] **Step 3: Implement the condensed profile surface**

Create local role/status label maps typed from `UserResponse`. Render one identity summary followed by a bordered definition-list surface. Keep edit fields local to the basic-info section, preserve current mutation/cache behavior, disable actions during save, and expose errors with `role="alert"`.

- [ ] **Step 4: Align preferences and notifications with the same row system**

Replace nested card-per-control styling with one titled surface containing divided rows. Preserve all settings queries, dirty state, reset, switch semantics, and save/error behavior; no new preference fields are introduced.

- [ ] **Step 5: Remove the unsupported destructive account action**

Keep password editing and the truthful unavailable two-step-verification message. Remove the “删除账户” button and its irreversible-copy block because no backend contract exists.

- [ ] **Step 6: Run account tests and verify GREEN**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/account-center.test.tsx src/features/account/tests/profile-section.test.tsx`

Expected: all selected account tests PASS.

### Task 6: Full verification and project records

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Run formatting check**

Run: `pnpm --filter @warmy/web format`

Expected: exit 0. If it reports changed files, run the repository formatter only on task files, then repeat the check.

- [ ] **Step 2: Run all Web unit/component tests**

Run: `pnpm --filter @warmy/web test`

Expected: exit 0 with zero failed tests. Any pre-existing failure must be reported with exact test names and must not be hidden.

- [ ] **Step 3: Run static verification**

Run: `pnpm --filter @warmy/web lint && pnpm --filter @warmy/web typecheck`

Expected: exit 0 for both commands.

- [ ] **Step 4: Run production build**

Run: `pnpm --filter @warmy/web build`

Expected: exit 0 and all help/account routes compile.

- [ ] **Step 5: Inspect responsive class invariants**

Review the final diff and confirm the shared shells include `min-w-0`, mobile overflow navigation, responsive columns, and no fixed content widths that exceed the viewport. The user declined browser visual tooling, so this is a code-level responsive inspection rather than screenshot QA.

- [ ] **Step 6: Update repository records**

Move TASK-20260629-006 from “当前进行中” to “已完成” only if every required verification passes. Otherwise set it to “待验证” and record exact failures, commands, and risk. Set `docs/当前任务.md` to “当前无活动任务” only on full completion.
