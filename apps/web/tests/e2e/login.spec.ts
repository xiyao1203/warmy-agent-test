import { expect, test, type Page } from "@playwright/test";

const projectId = "landing-project";

async function mockLoggedOutLanding(page: Page) {
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { detail: "Not authenticated" },
      status: 401,
    });
  });
}

async function mockSuccessfulLogin(page: Page) {
  await mockLoggedOutLanding(page);
  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        display_name: "Landing Reviewer",
        email: "reviewer@warmy.test",
        id: "reviewer-1",
        must_change_password: false,
        role: "project_admin",
        status: "active",
      },
    });
  });
  await page.route("**/api/v1/projects**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        items: [
          {
            archived: false,
            created_at: "2026-07-20T00:00:00Z",
            created_by: "reviewer-1",
            description: "Landing interaction verification",
            id: projectId,
            key: "LANDING",
            lead_user_id: "reviewer-1",
            name: "Landing Project",
            status: "active",
            updated_at: "2026-07-20T00:00:00Z",
            updated_by: "reviewer-1",
          },
        ],
        next_cursor: null,
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      },
    });
  });
}

async function assertNoHorizontalOverflow(page: Page) {
  const widths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(widths.scroll).toBeLessThanOrEqual(widths.client);
}

test.describe("项目导航", () => {
  test("登录页可正常渲染并导航", async ({ page }) => {
    await mockLoggedOutLanding(page);
    await page.goto("/login");
    await expect(
      page.getByRole("heading", { name: "Warmy Agent Test", level: 1 }),
    ).toBeVisible();

    await page.getByRole("button", { name: "登录", exact: true }).click();

    await expect(
      page.getByRole("heading", { name: "登录测试工作台" }),
    ).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();
  });

  test("pending session keeps landing entry copy stable", async ({
    page,
  }, testInfo) => {
    let releaseSession!: () => void;
    const sessionGate = new Promise<void>((resolve) => {
      releaseSession = resolve;
    });
    await page.setViewportSize({ height: 900, width: 1440 });
    await page.route("**/api/v1/auth/me", async (route) => {
      await sessionGate;
      await route.fulfill({
        contentType: "application/json",
        json: { detail: "Not authenticated" },
        status: 401,
      });
    });

    await page.goto("/login");

    const headerEntry = page.getByRole("button", {
      exact: true,
      name: "登录",
    });
    const heroEntry = page.getByRole("button", { name: "登录并开始" });
    await expect(page.getByText("正在检查")).toHaveCount(0);
    await expect(headerEntry).toBeDisabled();
    await expect(headerEntry).toHaveAttribute("aria-busy", "true");
    await expect(heroEntry).toBeDisabled();
    await expect(heroEntry).toHaveAttribute("aria-busy", "true");
    await page.screenshot({
      path: testInfo.outputPath("landing-pending-session-1440.png"),
    });

    releaseSession();
    await expect(headerEntry).toBeEnabled();
    await expect(headerEntry).toHaveAttribute("aria-busy", "false");
    await expect(heroEntry).toBeEnabled();
    await expect(heroEntry).toHaveAttribute("aria-busy", "false");
    await expect(page.getByText("正在检查")).toHaveCount(0);
  });

  test("登录成功停留落地页，用户确认后再进入工作台", async ({ page }) => {
    await mockSuccessfulLogin(page);
    await page.goto("/login");
    await page.getByRole("button", { name: "登录", exact: true }).click();

    const dialog = page.getByRole("dialog", { name: "登录测试工作台" });
    await dialog.getByLabel("邮箱").fill("reviewer@warmy.test");
    await dialog
      .getByRole("textbox", { name: "密码", exact: true })
      .fill("correct-password");
    await dialog.getByRole("button", { name: "登录", exact: true }).click();

    await expect(dialog).toBeHidden();
    await expect(page).toHaveURL(/\/login$/);
    await expect(
      page.getByRole("button", { name: "进入工作台", exact: true }),
    ).toBeVisible();

    await page.getByRole("button", { name: "进入工作台", exact: true }).click();
    await expect(page).toHaveURL(`/projects/${projectId}/test-agent`);
  });

  test("无登录访问项目页有内容", async ({ page }) => {
    await page.goto("/projects/test/overview");
    // 页面不应白屏
    await expect(page.locator("body")).toBeVisible();
  });
});

for (const width of [390, 1280, 1440, 1920]) {
  test(`落地页在 ${width}px 保持紧凑且无页面溢出`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ height: width === 390 ? 844 : 900, width });
    await mockLoggedOutLanding(page);
    await page.goto("/login");

    await expect(
      page.getByRole("heading", { name: "Warmy Agent Test", level: 1 }),
    ).toBeVisible();
    const evidence = page.getByRole("region", { name: "真实运行证据" });
    await expect(evidence).toBeVisible();
    await expect(evidence.locator(".precision-metric-card")).toHaveCount(4);
    await assertNoHorizontalOverflow(page);

    const cardLayout = await evidence
      .locator(".precision-metric-card")
      .evaluateAll((cards) =>
        cards.map((card) => {
          const rect = card.getBoundingClientRect();
          return { height: rect.height, top: rect.top };
        }),
      );
    expect(
      Math.max(...cardLayout.map(({ height }) => height)),
    ).toBeLessThanOrEqual(width === 390 ? 84 : 88);
    if (width === 390) {
      expect(new Set(cardLayout.map(({ top }) => Math.round(top))).size).toBe(
        2,
      );
      const clippedValues = await evidence
        .locator(".precision-metric-value")
        .evaluateAll(
          (values) =>
            values.filter((value) => value.scrollWidth > value.clientWidth)
              .length,
        );
      expect(clippedValues).toBe(0);
    } else {
      expect(new Set(cardLayout.map(({ top }) => Math.round(top))).size).toBe(
        1,
      );
    }

    if (width === 390 || width === 1440) {
      await page.screenshot({
        fullPage: true,
        path: testInfo.outputPath(`landing-${width}.png`),
      });
    }
  });
}

test.describe("运行中心", () => {
  test("运行中心页面导航", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toBeVisible();
    // 验证页面不崩溃即可
  });
});
