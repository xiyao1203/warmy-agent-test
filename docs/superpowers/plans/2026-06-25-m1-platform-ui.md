# M1 Platform UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付方案 1 视觉方向下可运行的登录、平台壳、项目切换、项目概览和超级管理员用户管理界面。

**Architecture:** Next.js App Router 页面只组合 Feature；`features/auth`、`features/projects`、`features/users` 分别封装业务状态和 API 调用；共享布局与 UI 组件不依赖 Feature。浏览器请求统一通过生成的 API Client，Cookie 自动携带，写操作由统一客户端读取 CSRF Cookie 并附加请求头。

**Tech Stack:** Next.js 16、React 19、TypeScript、TanStack Query、React Hook Form、Zod、Radix UI、Tailwind CSS、Vitest、Testing Library、生成的 Hey API Client。

---

## File Structure

```text
apps/web/src/
├── app/
│   ├── (auth)/login/page.tsx
│   ├── (platform)/layout.tsx
│   ├── (platform)/projects/[projectId]/overview/page.tsx
│   ├── (platform)/system/users/page.tsx
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── layout/app-shell.tsx
│   └── ui/{badge,dialog,drawer,dropdown-menu,empty-state,input,table}.tsx
├── features/
│   ├── auth/{api,login-form,session,index}.tsx
│   ├── projects/{api,project-overview,project-switcher,index}.tsx
│   └── users/{api,user-dialog,user-drawer,user-management,index}.tsx
├── lib/
│   ├── api/{client,csrf,problem}.ts
│   ├── permissions/index.ts
│   └── query/provider.tsx
└── test/factories.ts
```

`apps/web` 依赖 `@warmy/generated-api-client` 的 Workspace 包，不复制生成类型。

### Task 1: Install UI Dependencies and Establish API Infrastructure

**Files:**
- Modify: `apps/web/package.json`
- Modify: `pnpm-lock.yaml`
- Create: `apps/web/src/lib/api/csrf.ts`
- Create: `apps/web/src/lib/api/client.ts`
- Create: `apps/web/src/lib/api/problem.ts`
- Create: `apps/web/src/lib/query/provider.tsx`
- Modify: `apps/web/src/app/layout.tsx`
- Test: `apps/web/src/lib/api/client.test.ts`

- [ ] **Step 1: Write the failing API client test**

```ts
import { describe, expect, it } from "vitest";
import { csrfHeaders, readCookie } from "./csrf";

describe("csrf helpers", () => {
  it("reads and decodes the CSRF cookie", () => {
    expect(readCookie("csrf_token", "a=1; csrf_token=hello%20world")).toBe(
      "hello world",
    );
  });

  it("adds the CSRF header for mutations", () => {
    expect(csrfHeaders("csrf-token")).toEqual({
      "x-csrf-token": "csrf-token",
    });
  });
});
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
pnpm --filter @warmy/web test -- src/lib/api/client.test.ts
```

Expected: FAIL because `./csrf` does not exist.

- [ ] **Step 3: Add pinned dependencies**

Add:

```json
"@radix-ui/react-dialog": "1.1.17",
"@radix-ui/react-dropdown-menu": "2.1.18",
"@radix-ui/react-popover": "1.1.17",
"@warmy/generated-api-client": "workspace:*"
```

Run:

```bash
pnpm install
```

- [ ] **Step 4: Implement the CSRF and API helpers**

```ts
export function readCookie(name: string, source = document.cookie) {
  const prefix = `${encodeURIComponent(name)}=`;
  const value = source
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix))
    ?.slice(prefix.length);
  return value ? decodeURIComponent(value) : undefined;
}

export function csrfHeaders(token = readCookie("csrf_token")) {
  return token ? { "x-csrf-token": token } : {};
}
```

Create one browser client with `NEXT_PUBLIC_CONTROL_API_URL ?? "http://localhost:8000"` and export `apiClient`. Add a `QueryProvider` whose QueryClient disables automatic mutation retries and retries queries once.

- [ ] **Step 5: Wrap the root layout and verify GREEN**

Wrap `children` in `QueryProvider`.

Run:

```bash
pnpm --filter @warmy/web test -- src/lib/api/client.test.ts
pnpm --filter @warmy/web typecheck
```

Expected: tests and typecheck PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/web/package.json apps/web/src/lib apps/web/src/app/layout.tsx pnpm-lock.yaml
git commit -m "build(web): add API and query infrastructure"
```

### Task 2: Build Accessible Shared UI Primitives

**Files:**
- Modify: `apps/web/src/components/ui/button.tsx`
- Create: `apps/web/src/components/ui/input.tsx`
- Create: `apps/web/src/components/ui/badge.tsx`
- Create: `apps/web/src/components/ui/dialog.tsx`
- Create: `apps/web/src/components/ui/drawer.tsx`
- Create: `apps/web/src/components/ui/dropdown-menu.tsx`
- Create: `apps/web/src/components/ui/table.tsx`
- Create: `apps/web/src/components/ui/empty-state.tsx`
- Modify: `apps/web/src/styles/tokens.css`
- Modify: `apps/web/src/app/globals.css`
- Test: `apps/web/src/components/ui/dialog.test.tsx`

- [ ] **Step 1: Write the failing dialog focus test**

Render a Dialog with trigger `创建用户`, open it, assert `role="dialog"` and its first input receive focus, close it, and assert focus returns to the trigger.

- [ ] **Step 2: Run the test and verify RED**

```bash
pnpm --filter @warmy/web test -- src/components/ui/dialog.test.tsx
```

Expected: FAIL because `dialog.tsx` does not exist.

- [ ] **Step 3: Implement the primitives**

Use Radix Dialog for both `Dialog` and right-aligned `Drawer`, Radix Dropdown Menu for action menus, semantic `<table>` elements for Table, and existing Lucide icons. Components accept `className` and forward relevant native props.

Add semantic tokens for overlay, selected row, disabled text, shadow, radius and control height. Do not add raw product colors to pages.

- [ ] **Step 4: Verify GREEN**

```bash
pnpm --filter @warmy/web test -- src/components/ui/dialog.test.tsx
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/ui apps/web/src/styles apps/web/src/app/globals.css
git commit -m "feat(web): add accessible interface primitives"
```

### Task 3: Implement Login and Session Access

**Files:**
- Create: `apps/web/src/features/auth/api.ts`
- Create: `apps/web/src/features/auth/login-form.tsx`
- Create: `apps/web/src/features/auth/session.ts`
- Create: `apps/web/src/features/auth/index.ts`
- Create: `apps/web/src/features/auth/tests/login-form.test.tsx`
- Create: `apps/web/src/app/(auth)/login/page.tsx`
- Modify: `apps/web/src/app/page.tsx`

- [ ] **Step 1: Write failing login tests**

Cover:

```ts
it("validates email and password before submitting")
it("shows one generic message for authentication failure")
it("disables repeated submission while login is pending")
it("passes the preserved return URL after success")
```

Inject an `onLogin` function into `LoginForm` so tests use real form behavior without mocking generated internals.

- [ ] **Step 2: Run tests and verify RED**

```bash
pnpm --filter @warmy/web test -- src/features/auth/tests/login-form.test.tsx
```

Expected: FAIL because `LoginForm` does not exist.

- [ ] **Step 3: Implement the auth API**

`login(credentials)` calls `loginApiV1AuthLoginPost({ client: apiClient, body })`.
`getCurrentUser()` calls `currentUserApiV1AuthMeGet`.
`logout()` calls the generated logout method with `csrfHeaders()`.

Normalize all authentication failures to:

```text
邮箱或密码不正确，请重试。
```

- [ ] **Step 4: Implement the login page**

Build the compact scheme-1 login surface with labeled email/password fields, show-password button, inline validation, pending state and accessible error summary. Validate `returnTo` as an internal path beginning with `/`; otherwise use `/`.

Root `/` redirects to `/login` until platform session routing is active.

- [ ] **Step 5: Verify GREEN**

```bash
pnpm --filter @warmy/web test -- src/features/auth/tests/login-form.test.tsx
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/features/auth apps/web/src/app
git commit -m "feat(web): add secure login experience"
```

### Task 4: Implement Permissions, Platform Shell and Project Switcher

**Files:**
- Create: `apps/web/src/lib/permissions/index.ts`
- Modify: `apps/web/src/components/layout/app-shell.tsx`
- Create: `apps/web/src/features/projects/api.ts`
- Create: `apps/web/src/features/projects/project-switcher.tsx`
- Create: `apps/web/src/features/projects/index.ts`
- Create: `apps/web/src/features/projects/tests/project-switcher.test.tsx`
- Create: `apps/web/src/components/layout/app-shell.test.tsx`
- Create: `apps/web/src/app/(platform)/layout.tsx`

- [ ] **Step 1: Write failing permission and switcher tests**

Cover:

```ts
expect(canManageUsers(superAdmin)).toBe(true);
expect(canManageUsers(developer)).toBe(false);
expect(screen.queryByText("系统管理")).not.toBeInTheDocument();
expect(screen.getByRole("option", { name: "项目 A" })).toBeVisible();
expect(screen.queryByText("未授权项目")).not.toBeInTheDocument();
```

- [ ] **Step 2: Run tests and verify RED**

```bash
pnpm --filter @warmy/web test -- src/features/projects/tests/project-switcher.test.tsx src/components/layout/app-shell.test.tsx
```

Expected: FAIL because permission and project Feature files do not exist.

- [ ] **Step 3: Implement permissions and project API**

`canManageUsers(user)` returns `user.role === "super_admin"`.
`listProjects()` uses the generated project list SDK.

- [ ] **Step 4: Implement the scheme-1 platform shell**

Use a compact 48px header, 224px sidebar and flexible main region. Render only M1-operable links:

- 项目概览
- 用户管理 for super administrators

Keep a `workspaceMode?: "management" | "agent"` prop so a future Agent route can render a right context column without replacing the shell.

- [ ] **Step 5: Implement the project switcher**

Use Radix Popover, searchable authorized project list, active/archived labels, selected indicator and internal route navigation to `/projects/{id}/overview`.

- [ ] **Step 6: Verify GREEN**

```bash
pnpm --filter @warmy/web test -- src/features/projects/tests/project-switcher.test.tsx src/components/layout/app-shell.test.tsx
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/lib/permissions apps/web/src/components/layout apps/web/src/features/projects apps/web/src/app/\(platform\)/layout.tsx
git commit -m "feat(web): add project-aware platform shell"
```

### Task 5: Build Project Overview

**Files:**
- Create: `apps/web/src/features/projects/project-overview.tsx`
- Create: `apps/web/src/features/projects/tests/project-overview.test.tsx`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/overview/page.tsx`
- Modify: `apps/web/src/features/projects/index.ts`

- [ ] **Step 1: Write failing overview tests**

Cover loading, service error, inaccessible project, archived project, member summary and honest empty test-activity state.

- [ ] **Step 2: Run tests and verify RED**

```bash
pnpm --filter @warmy/web test -- src/features/projects/tests/project-overview.test.tsx
```

Expected: FAIL because `ProjectOverview` does not exist.

- [ ] **Step 3: Implement project queries**

Use generated `getProjectApiV1ProjectsProjectIdGet` and `listMembersApiV1ProjectsProjectIdMembersGet`. Map 404 to one neutral “项目不存在或你无权访问” state.

- [ ] **Step 4: Implement the overview**

Render project name, archived state, project ID, current access summary, member count/list and an empty state explaining that Agent/test activity will appear after M2 assets are created. Do not invent metrics.

- [ ] **Step 5: Verify GREEN and commit**

```bash
pnpm --filter @warmy/web test -- src/features/projects/tests/project-overview.test.tsx
pnpm --filter @warmy/web typecheck
git add apps/web/src/features/projects apps/web/src/app/\(platform\)/projects
git commit -m "feat(web): add project overview"
```

### Task 6: Build User Management Table and Detail Drawer

**Files:**
- Create: `apps/web/src/features/users/api.ts`
- Create: `apps/web/src/features/users/user-management.tsx`
- Create: `apps/web/src/features/users/user-drawer.tsx`
- Create: `apps/web/src/features/users/index.ts`
- Create: `apps/web/src/features/users/tests/user-management.test.tsx`
- Create: `apps/web/src/app/(platform)/system/users/page.tsx`

- [ ] **Step 1: Write failing table-state tests**

Cover loading, empty, no-search-results, error, permission, populated rows, role/status badges, opening the selected user drawer, and absence of unsafe current-admin controls.

- [ ] **Step 2: Run tests and verify RED**

```bash
pnpm --filter @warmy/web test -- src/features/users/tests/user-management.test.tsx
```

Expected: FAIL because user Feature files do not exist.

- [ ] **Step 3: Implement user queries**

Use generated list/get SDK methods. Keep keyword/role/status filtering client-side for the current API page because the backend contract only exposes cursor and limit. Do not claim server filtering.

- [ ] **Step 4: Implement the dense management surface**

Render page heading, create action, compact filters, semantic table, role/status badges, pagination affordance from `next_cursor`, and a right-side Drawer. The drawer contains identity, role, status and protected operations.

- [ ] **Step 5: Verify GREEN**

```bash
pnpm --filter @warmy/web test -- src/features/users/tests/user-management.test.tsx
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/features/users apps/web/src/app/\(platform\)/system/users
git commit -m "feat(web): add user management workspace"
```

### Task 7: Add User Mutations and Safety Confirmations

**Files:**
- Create: `apps/web/src/features/users/user-dialog.tsx`
- Create: `apps/web/src/features/users/tests/user-actions.test.tsx`
- Modify: `apps/web/src/features/users/api.ts`
- Modify: `apps/web/src/features/users/user-management.tsx`
- Modify: `apps/web/src/features/users/user-drawer.tsx`

- [ ] **Step 1: Write failing mutation tests**

Cover create form validation, retained values after server error, reset-password impact text, disable impact text, explicit action labels, current-user protection and successful list refresh.

- [ ] **Step 2: Run tests and verify RED**

```bash
pnpm --filter @warmy/web test -- src/features/users/tests/user-actions.test.tsx
```

Expected: FAIL because mutation dialogs are absent.

- [ ] **Step 3: Implement mutation APIs**

Use generated create, update, reset password, disable, enable and delete SDK calls. Every mutation passes `csrfHeaders()`. Convert 403/404/409/422 into stable UI problem categories while preserving safe server detail for conflicts.

- [ ] **Step 4: Implement dialogs and refresh behavior**

Use React Hook Form + Zod. After successful mutation, invalidate `["users"]`, close the dialog and keep/open the affected drawer. Never store a generated or entered password outside current component state.

- [ ] **Step 5: Verify GREEN and commit**

```bash
pnpm --filter @warmy/web test -- src/features/users/tests/user-actions.test.tsx
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
git add apps/web/src/features/users
git commit -m "feat(web): add protected user administration actions"
```

### Task 8: Visual Verification, Documentation and Task Handoff

**Files:**
- Create: `design-qa.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Run the full web verification**

```bash
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
make api-check
```

Expected: PASS.

- [ ] **Step 2: Run the app and capture scheme-1 states**

Capture at 1440×1024:

- `/login`
- project overview with project switcher open
- `/system/users` with detail drawer open

Use the in-app browser and the selected scheme-1 reference image.

- [ ] **Step 3: Run Product Design QA**

Compare source and implementation at the same viewport. Record issues in `design-qa.md`; fix P0/P1/P2 issues and repeat until:

```text
final result: passed
```

- [ ] **Step 4: Update the task ledger**

Mark Task 14 complete only if component verification and design QA pass. Record any backend/Docker/E2E gaps under Task 15.

- [ ] **Step 5: Commit**

```bash
git add apps/web design-qa.md docs/当前任务.md docs/开发进度与变更记录.md
git commit -m "feat(web): complete m1 platform interface"
```

## Plan Self-Review

- Spec coverage: login, shell, project switching, project overview, user CRUD entry points, permissions, async states, accessibility and future Agent three-column layout are assigned to Tasks 1–8.
- Scope: no Agent streaming business logic, test assets or fabricated run data are introduced.
- Type consistency: generated names and payloads match the current OpenAPI client (`UserResponse`, `ProjectResponse`, `SystemRole`, `UserStatus`).
- Dependency check: Radix versions were resolved from the official npm registry on 2026-06-25 and will be locked in `pnpm-lock.yaml`.
