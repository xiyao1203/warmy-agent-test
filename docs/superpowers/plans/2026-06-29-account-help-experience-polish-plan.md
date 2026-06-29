# Unified Account and Help Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved A-direction unified account center and make help, feedback, notification, and user-menu interactions fully functional against the existing backend APIs.

**Architecture:** Recover the merge-corrupted control API first, then expose its existing profile, password, user-settings, and feedback contracts through the generated TypeScript client. The web app gains focused `account`, `help`, and layout components; route pages remain composition boundaries, while API calls and mutation state live in Feature modules.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, pytest, Next.js App Router, React 19, TanStack Query, Radix UI, Lucide, Vitest/Testing Library, Playwright, Tailwind CSS 4.

---

## File map

Backend recovery and contracts:

- Modify `apps/control-api/src/agenttest/modules/identity/api/router.py`: retain the canonical auth router and add profile/password mutations with CSRF validation.
- Modify `apps/control-api/src/agenttest/modules/identity/api/schemas.py`: keep one schema module and add profile/password request models once.
- Modify `apps/control-api/src/agenttest/bootstrap/app.py`: keep the canonical application bootstrap and register user-settings and feedback dependencies once.
- Modify `apps/control-api/src/agenttest/modules/user_settings/api/router.py`: require CSRF for settings mutations.
- Modify `apps/control-api/src/agenttest/modules/reports/api/router.py`: remove the duplicate module body that prevents compilation while preserving the registered report-router contract.
- Create `apps/control-api/tests/architecture/test_source_compilation.py`: guard against future concatenated Python modules.
- Modify `apps/control-api/tests/contract/test_auth_api.py`: cover profile/password contracts and CSRF.
- Create `apps/control-api/tests/contract/test_user_settings_api.py`: cover defaults, update, validation, authentication, and CSRF.
- Create `apps/control-api/tests/contract/test_feedback_api.py`: cover authenticated and anonymous feedback creation.

Frontend account experience:

- Create `apps/web/src/features/account/api.ts`: generated-client wrappers for profile, password, and settings.
- Create `apps/web/src/features/account/types.ts`: account section and editable settings types.
- Create `apps/web/src/features/account/account-center.tsx`: query-param section routing and responsive two-column shell.
- Create `apps/web/src/features/account/profile-section.tsx`: profile summary and edit state.
- Create `apps/web/src/features/account/preferences-section.tsx`: appearance and language settings with dirty-state controls.
- Create `apps/web/src/features/account/notifications-section.tsx`: notification preferences and browser-permission state.
- Create `apps/web/src/features/account/security-section.tsx`: password dialog and unavailable-capability explanations.
- Create `apps/web/src/features/account/password-dialog.tsx`: focused password form.
- Create `apps/web/src/features/account/index.ts`: public Feature exports.
- Create tests in `apps/web/src/features/account/tests/` for navigation, profile, settings, and password behavior.
- Create `apps/web/src/app/(platform)/account/page.tsx`: account route composition.
- Replace `apps/web/src/app/(platform)/profile/page.tsx` and `settings/page.tsx` with compatibility redirects.

Frontend top-bar and support experience:

- Refactor `apps/web/src/components/layout/help-dropdown.tsx` and `user-dropdown.tsx` to Radix menu primitives.
- Create `apps/web/src/components/layout/notification-dropdown.tsx` with truthful empty state and preferences link.
- Modify `apps/web/src/components/layout/app-shell.tsx` and its test.
- Create `apps/web/src/features/help/help-search.tsx`, `help-faq.tsx`, `feedback-form.tsx`, `api.ts`, and `index.ts`.
- Create `apps/web/src/app/(help)/help-shell.tsx` and refactor the help layout/pages to use it.
- Refactor `apps/web/src/app/(help)/docs/page.tsx` and `feedback/page.tsx` around the Help Feature.
- Create focused help/feedback component tests and `apps/web/playwright/account-help.spec.ts`.

Documentation and visual QA:

- Update `docs/当前任务.md` and `docs/开发进度与变更记录.md` with verification evidence.
- Create `design-qa.md` and optimized screenshots in `docs/ui-audits/2026-06-29-account-experience/`.

---

### Task 1: Recover the control API and lock the regression

**Files:**
- Create: `apps/control-api/tests/architecture/test_source_compilation.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/api/schemas.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/src/agenttest/modules/reports/api/router.py`
- Test: `apps/control-api/tests/architecture/test_source_compilation.py`

- [ ] **Step 1: Write the failing source-compilation regression test**

```python
from pathlib import Path
import py_compile


def test_all_control_api_sources_compile() -> None:
    source_root = Path(__file__).parents[2] / "src"
    failures: list[str] = []
    for source in source_root.rglob("*.py"):
        try:
            py_compile.compile(source, doraise=True)
        except py_compile.PyCompileError as error:
            failures.append(f"{source}: {error.msg}")
    assert failures == []
```

- [ ] **Step 2: Run the regression test and verify RED**

Run: `uv run pytest apps/control-api/tests/architecture/test_source_compilation.py -q`

Expected: FAIL listing the second `from __future__ import annotations` in identity and report routers.

- [ ] **Step 3: Restore one canonical module body per corrupted file**

Use the first parent of merge `4dd55c3` as the known-good base, then apply only the intended profile/settings/feedback additions. The identity dependency shape must be exactly:

```python
@dataclass(frozen=True, slots=True)
class AuthApiDependencies:
    login: LoginExecutor
    current_user: CurrentUserExecutor
    logout: LogoutExecutor
    csrf: CsrfExecutor
    update_profile: UpdateProfileExecutor
    change_password: ChangePasswordExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory
```

The bootstrap must register each router once:

```python
user_settings = user_settings_dependencies or build_user_settings_dependencies(
    resolved_settings
)
app.include_router(
    create_user_settings_router(user_settings, resolved_settings),
    prefix="/api/v1",
)

feedback = feedback_dependencies or build_feedback_dependencies(resolved_settings)
app.include_router(
    create_feedback_router(feedback, resolved_settings),
    prefix="/api/v1",
)
```

- [ ] **Step 4: Verify GREEN and run import smoke tests**

Run: `uv run pytest apps/control-api/tests/architecture/test_source_compilation.py apps/control-api/tests/contract/test_health.py -q`

Expected: both tests PASS and `create_app()` imports successfully.

- [ ] **Step 5: Commit the recovery separately**

```bash
git add apps/control-api/src/agenttest apps/control-api/tests/architecture/test_source_compilation.py
git commit -m "fix: recover control api after malformed merge"
```

### Task 2: Secure and verify account-support API contracts

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/identity/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/user_settings/api/router.py`
- Modify: `apps/control-api/tests/contract/test_auth_api.py`
- Create: `apps/control-api/tests/contract/test_user_settings_api.py`
- Create: `apps/control-api/tests/contract/test_feedback_api.py`

- [ ] **Step 1: Add failing contract tests for mutation CSRF and responses**

Add profile coverage with explicit expectations:

```python
def test_profile_update_requires_csrf_and_returns_updated_user() -> None:
    client, updater = authenticated_client()
    payload = {"display_name": "Updated User", "email": "updated@example.com"}

    assert client.patch("/api/v1/auth/me", json=payload).status_code == 403
    response = client.patch(
        "/api/v1/auth/me",
        json=payload,
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated User"
    assert updater.calls == [("Updated User", "updated@example.com")]
```

Add settings mutation coverage:

```python
def test_settings_update_requires_csrf_and_returns_persisted_values() -> None:
    client = settings_client()
    payload = {"theme": "light", "language": "zh-CN", "email_notifications": False}
    assert client.patch("/api/v1/users/me/settings", json=payload).status_code == 403
    response = client.patch(
        "/api/v1/users/me/settings",
        json=payload,
        headers={"X-CSRF-Token": "csrf-token"},
    )
    assert response.status_code == 200
    assert response.json()["email_notifications"] is False
```

- [ ] **Step 2: Run focused contracts and verify RED**

Run: `uv run pytest apps/control-api/tests/contract/test_auth_api.py apps/control-api/tests/contract/test_user_settings_api.py apps/control-api/tests/contract/test_feedback_api.py -q`

Expected: FAIL because new dependencies/contracts and CSRF checks are absent or incomplete.

- [ ] **Step 3: Implement one shared CSRF validation path for account mutations**

Profile, password, and settings mutations must validate the session token, CSRF cookie, header, and validator before executing their handlers:

```python
async def require_csrf(
    request: Request,
    session_token: str,
    csrf_header: str | None,
    csrf: CsrfExecutor,
) -> JSONResponse | None:
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf_header or not csrf_cookie or csrf_header != csrf_cookie:
        return problem_response(
            status=403,
            title="CSRF validation failed",
            detail="A valid CSRF token is required",
        )
    try:
        await csrf.execute(session_token, csrf_header)
    except InvalidSessionError:
        return problem_response(
            status=403,
            title="CSRF validation failed",
            detail="A valid CSRF token is required",
        )
    return None
```

- [ ] **Step 4: Run contracts and related identity tests**

Run: `uv run pytest apps/control-api/tests/contract/test_auth_api.py apps/control-api/tests/contract/test_user_settings_api.py apps/control-api/tests/contract/test_feedback_api.py apps/control-api/tests/unit/identity -q`

Expected: all selected tests PASS.

- [ ] **Step 5: Commit API contracts**

```bash
git add apps/control-api/src/agenttest/modules/identity apps/control-api/src/agenttest/modules/user_settings apps/control-api/tests/contract
git commit -m "feat: secure account and feedback api contracts"
```

### Task 3: Regenerate the client and create the Account Feature API

**Files:**
- Modify: `packages/generated-api-client/src/`
- Create: `apps/web/src/features/account/api.ts`
- Create: `apps/web/src/features/account/types.ts`
- Create: `apps/web/src/features/account/index.ts`
- Test: `apps/web/src/features/account/tests/api.test.ts`

- [ ] **Step 1: Write failing wrapper tests**

```typescript
it("sends CSRF headers when updating the profile", async () => {
  apiMocks.updateProfile.mockResolvedValue({ data: user });
  await updateProfile({ display_name: "New Name", email: "user@example.com" });
  expect(apiMocks.updateProfile).toHaveBeenCalledWith(
    expect.objectContaining({ headers: { "x-csrf-token": "csrf-token" } }),
  );
});
```

- [ ] **Step 2: Run wrapper tests and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/api.test.ts`

Expected: FAIL because `@/features/account` does not exist.

- [ ] **Step 3: Regenerate the OpenAPI client**

Run the control API locally, then run: `pnpm api:generate`

Expected: generated operations include update profile, change password, get/update settings, and create feedback.

- [ ] **Step 4: Implement typed wrappers**

```typescript
export async function updateProfile(body: UpdateProfileRequest) {
  const { data } = await updateProfileApiV1AuthMePatch({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
  return data;
}

export async function updateUserSettings(body: UpdateSettingsRequest) {
  const { data } = await updateSettingsApiV1UsersMeSettingsPatch({
    body,
    client: apiClient,
    headers: csrfHeaders(),
    throwOnError: true,
  });
  return data;
}
```

- [ ] **Step 5: Verify wrappers and type generation**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/api.test.ts && pnpm --filter @warmy/web typecheck`

Expected: PASS.

- [ ] **Step 6: Commit generated client and Feature boundary**

```bash
git add packages/generated-api-client apps/web/src/features/account
git commit -m "feat: add account api client"
```

### Task 4: Build the responsive account-center shell

**Files:**
- Create: `apps/web/src/features/account/account-center.tsx`
- Create: `apps/web/src/features/account/tests/account-center.test.tsx`
- Create: `apps/web/src/app/(platform)/account/page.tsx`
- Modify: `apps/web/src/app/(platform)/profile/page.tsx`
- Modify: `apps/web/src/app/(platform)/settings/page.tsx`

- [ ] **Step 1: Write failing navigation and route-compatibility tests**

```typescript
it("shows the section from the query string and exposes all account sections", () => {
  render(<AccountCenter initialSection="notifications" user={user} />);
  expect(screen.getByRole("heading", { name: "通知设置" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "个人资料" })).toHaveAttribute(
    "href",
    "/account?section=profile",
  );
});
```

- [ ] **Step 2: Verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/account-center.test.tsx`

Expected: FAIL because the account-center component and route do not exist.

- [ ] **Step 3: Implement the A-direction shell**

```typescript
export type AccountSection = "profile" | "preferences" | "notifications" | "security";

const sections = [
  { id: "profile", label: "个人资料", href: "/account?section=profile" },
  { id: "preferences", label: "偏好设置", href: "/account?section=preferences" },
  { id: "notifications", label: "通知设置", href: "/account?section=notifications" },
  { id: "security", label: "账号安全", href: "/account?section=security" },
] satisfies ReadonlyArray<{ id: AccountSection; label: string; href: string }>;
```

Use a `lg:grid-cols-[13rem_minmax(0,1fr)]` desktop layout and a scrollable segmented navigation below `lg`; the main container must include `min-w-0` and page-level `overflow-x-hidden` safeguards.

- [ ] **Step 4: Add compatibility redirects**

```typescript
import { redirect } from "next/navigation";

export default function ProfileCompatibilityPage() {
  redirect("/account?section=profile");
}
```

The settings route redirects to `/account?section=preferences`.

- [ ] **Step 5: Verify shell tests and typecheck**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests/account-center.test.tsx && pnpm --filter @warmy/web typecheck`

Expected: PASS.

- [ ] **Step 6: Commit the account shell**

```bash
git add apps/web/src/features/account apps/web/src/app/\(platform\)/account apps/web/src/app/\(platform\)/profile apps/web/src/app/\(platform\)/settings
git commit -m "feat: add unified account center shell"
```

### Task 5: Implement profile, preferences, notifications, and security sections

**Files:**
- Create: `apps/web/src/features/account/profile-section.tsx`
- Create: `apps/web/src/features/account/preferences-section.tsx`
- Create: `apps/web/src/features/account/notifications-section.tsx`
- Create: `apps/web/src/features/account/security-section.tsx`
- Create: `apps/web/src/features/account/password-dialog.tsx`
- Test: `apps/web/src/features/account/tests/profile-section.test.tsx`
- Test: `apps/web/src/features/account/tests/settings-sections.test.tsx`
- Test: `apps/web/src/features/account/tests/password-dialog.test.tsx`

- [ ] **Step 1: Write failing profile-edit behavior tests**

```typescript
it("keeps values on failure and exits edit mode after a successful save", async () => {
  updateProfileMock.mockRejectedValueOnce(new Error("保存失败"));
  render(<ProfileSection user={user} />);
  await userEvent.click(screen.getByRole("button", { name: "编辑资料" }));
  await userEvent.clear(screen.getByLabelText("显示名称"));
  await userEvent.type(screen.getByLabelText("显示名称"), "新名称");
  await userEvent.click(screen.getByRole("button", { name: "保存资料" }));
  expect(await screen.findByText("保存失败，请重试")).toBeInTheDocument();
  expect(screen.getByLabelText("显示名称")).toHaveValue("新名称");
});
```

- [ ] **Step 2: Write failing settings dirty-state and password tests**

```typescript
it("enables save only after settings change and reset restores server values", async () => {
  render(<PreferencesSection settings={serverSettings} />);
  expect(screen.getByRole("button", { name: "保存设置" })).toBeDisabled();
  await userEvent.click(screen.getByRole("radio", { name: "浅色" }));
  expect(screen.getByRole("button", { name: "保存设置" })).toBeEnabled();
  await userEvent.click(screen.getByRole("button", { name: "重置" }));
  expect(screen.getByRole("button", { name: "保存设置" })).toBeDisabled();
});
```

- [ ] **Step 3: Run focused tests and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests`

Expected: FAIL because section components are missing.

- [ ] **Step 4: Implement minimal sections with TanStack Query mutations**

All mutations use pending state, persistent inline errors, and cache updates. A switch must use explicit semantics:

```tsx
<button
  aria-checked={enabled}
  aria-label={label}
  onClick={() => onChange(!enabled)}
  role="switch"
  type="button"
>
  <span aria-hidden="true" />
</button>
```

The security section renders password management as functional; two-step verification and account deletion render explanatory unavailable states until backend contracts exist.

- [ ] **Step 5: Verify account section tests**

Run: `pnpm --filter @warmy/web test -- src/features/account/tests && pnpm --filter @warmy/web typecheck`

Expected: PASS with no React act warnings.

- [ ] **Step 6: Commit functional account sections**

```bash
git add apps/web/src/features/account
git commit -m "feat: complete account settings interactions"
```

### Task 6: Replace top-bar custom menus with accessible interactions

**Files:**
- Modify: `apps/web/src/components/layout/help-dropdown.tsx`
- Modify: `apps/web/src/components/layout/user-dropdown.tsx`
- Create: `apps/web/src/components/layout/notification-dropdown.tsx`
- Modify: `apps/web/src/components/layout/app-shell.tsx`
- Modify: `apps/web/src/components/layout/app-shell.test.tsx`
- Create: `apps/web/src/components/layout/account-dropdowns.test.tsx`

- [ ] **Step 1: Write failing menu semantics and truthful-notification tests**

```typescript
it("opens notifications with an empty state and a preferences link", async () => {
  render(<NotificationDropdown />);
  await userEvent.click(screen.getByRole("button", { name: "通知" }));
  expect(screen.getByText("暂无新通知")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "通知偏好" })).toHaveAttribute(
    "href",
    "/account?section=notifications",
  );
});
```

- [ ] **Step 2: Run tests and verify RED**

Run: `pnpm --filter @warmy/web test -- src/components/layout/account-dropdowns.test.tsx src/components/layout/app-shell.test.tsx`

Expected: FAIL because notifications are inert and account links still target legacy routes.

- [ ] **Step 3: Implement menus using Radix primitives**

Use `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, and `DropdownMenuItem` so arrow-key navigation, Escape, outside-click handling, and focus restoration come from the shared primitive. Internal help links open in the current tab; placeholder external links are removed.

- [ ] **Step 4: Verify menus and app shell**

Run: `pnpm --filter @warmy/web test -- src/components/layout/account-dropdowns.test.tsx src/components/layout/app-shell.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit top-bar interactions**

```bash
git add apps/web/src/components/layout
git commit -m "feat: polish account help and notification menus"
```

### Task 7: Build searchable help and real feedback submission

**Files:**
- Create: `apps/web/src/features/help/api.ts`
- Create: `apps/web/src/features/help/help-search.tsx`
- Create: `apps/web/src/features/help/help-faq.tsx`
- Create: `apps/web/src/features/help/feedback-form.tsx`
- Create: `apps/web/src/features/help/index.ts`
- Create: `apps/web/src/features/help/tests/help-search.test.tsx`
- Create: `apps/web/src/features/help/tests/feedback-form.test.tsx`
- Create: `apps/web/src/app/(help)/help-shell.tsx`
- Modify: `apps/web/src/app/(help)/layout.tsx`
- Modify: `apps/web/src/app/(help)/docs/page.tsx`
- Modify: `apps/web/src/app/(help)/feedback/page.tsx`

- [ ] **Step 1: Write failing search and feedback tests**

```typescript
it("filters help topics and offers recovery when no result matches", async () => {
  render(<HelpSearch topics={topics} />);
  await userEvent.type(screen.getByRole("searchbox"), "不存在的内容");
  expect(screen.getByText("没有找到相关内容")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "清空搜索" }));
  expect(screen.getAllByRole("link")).toHaveLength(topics.length);
});
```

```typescript
it("submits feedback once and exposes retry after a server error", async () => {
  submitFeedbackMock.mockRejectedValueOnce(new Error("network"));
  render(<FeedbackForm />);
  await fillValidFeedback();
  await userEvent.click(screen.getByRole("button", { name: "提交反馈" }));
  expect(await screen.findByText("提交失败，请重试")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "重新提交" })).toBeEnabled();
});
```

- [ ] **Step 2: Run tests and verify RED**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests`

Expected: FAIL because the Help Feature is missing.

- [ ] **Step 3: Implement help search, accessible FAQ, and feedback API wrapper**

```typescript
export async function submitFeedback(body: CreateFeedbackRequest) {
  const { data } = await createFeedbackApiV1FeedbackPost({
    body,
    client: apiClient,
    throwOnError: true,
  });
  return data;
}
```

Help content uses semantic headings, a real `type="search"` input, and native `details/summary` or an equivalent keyboard-operable accordion. Remove links to missing anchors and render only real destinations.

- [ ] **Step 4: Implement responsive Help Shell**

The shell has a sticky 56px header, desktop category navigation, `min-w-0` content, and a one-column mobile layout. It must not repeat or crop header/content when the browser width is below 400px.

- [ ] **Step 5: Verify help tests and build**

Run: `pnpm --filter @warmy/web test -- src/features/help/tests && pnpm --filter @warmy/web typecheck && pnpm --filter @warmy/web build`

Expected: PASS.

- [ ] **Step 6: Commit help and feedback**

```bash
git add apps/web/src/features/help apps/web/src/app/\(help\)
git commit -m "feat: make help search and feedback functional"
```

### Task 8: Browser E2E, design QA, and project records

**Files:**
- Create: `apps/web/playwright/account-help.spec.ts`
- Create: `design-qa.md`
- Create: `docs/ui-audits/2026-06-29-account-experience/account-center-final.png`
- Create: `docs/ui-audits/2026-06-29-account-experience/help-center-final.png`
- Create: `docs/ui-audits/2026-06-29-account-experience/help-center-mobile-final.png`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Write the failing critical-path E2E**

```typescript
test("account and help critical paths", async ({ page }) => {
  await page.goto("/account?section=profile");
  await expect(page.getByRole("heading", { name: "个人资料" })).toBeVisible();
  await page.getByRole("link", { name: "通知设置" }).click();
  await expect(page.getByRole("heading", { name: "通知设置" })).toBeVisible();
  await page.goto("/docs");
  await page.getByRole("searchbox").fill("Agent");
  await expect(page.getByText("Agent 管理")).toBeVisible();
});
```

- [ ] **Step 2: Run E2E and verify RED before the final wiring is complete**

Run: `pnpm --filter @warmy/web e2e -- account-help.spec.ts`

Expected: FAIL at the first missing/unwired critical interaction.

- [ ] **Step 3: Complete only the wiring required by the E2E and verify GREEN**

Run: `pnpm --filter @warmy/web e2e -- account-help.spec.ts`

Expected: PASS.

- [ ] **Step 4: Run the full verification matrix**

```text
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
uv run ruff check apps/control-api
uv run mypy apps/control-api/src
uv run pytest apps/control-api/tests/architecture/test_source_compilation.py apps/control-api/tests/contract/test_auth_api.py apps/control-api/tests/contract/test_user_settings_api.py apps/control-api/tests/contract/test_feedback_api.py
```

Expected: all commands PASS. Any environment-blocked verification is recorded explicitly rather than inferred.

- [ ] **Step 5: Run browser visual comparison and Design QA**

Open the approved A-direction reference and the implementation at matching desktop state and viewport, then repeat at a mobile viewport. Record findings in `design-qa.md`; fix P0/P1/P2 findings and repeat until the file ends with:

```text
final result: passed
```

- [ ] **Step 6: Update task/progress records and commit completion**

```bash
git add design-qa.md docs apps/web/playwright
git commit -m "test: verify account and help experience"
```
