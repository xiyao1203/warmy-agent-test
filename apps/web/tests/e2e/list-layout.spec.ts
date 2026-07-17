import { expect, test, type Page } from "@playwright/test";

const longName =
  "Mission Acceptance 超长项目名称用于验证列表一屏显示、文本完整提示能力以及极端用户输入不会撑破操作列的稳定布局";

async function mockProjectList(page: Page) {
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        email: "admin@agenttest.local",
        id: "admin-1",
        display_name: "Admin",
        role: "super_admin",
        status: "active",
        must_change_password: false,
      },
    });
  });
  await page.route("**/api/v1/projects", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        contentType: "application/json",
        json: {
          items: Array.from({ length: 8 }, (_, index) => ({
            active_environment_count: 1,
            agent_count: 2,
            archived: index === 7,
            created_at: "2026-07-16T00:00:00Z",
            created_by: "admin-1",
            dataset_count: 3,
            description: "覆盖专业测试资产与执行闭环的项目",
            id: `project-${index}-with-a-long-stable-identifier`,
            key: `MISSION-${index + 1}`,
            last_run: {
              href: `/projects/project-${index}-with-a-long-stable-identifier/runs/run-${index + 1}`,
              id: `run-${index + 1}`,
              key: `RUN-${String(index + 1).padStart(4, "0")}`,
              name: `RUN-${String(index + 1).padStart(4, "0")}`,
              type: "run",
            },
            last_run_at: "2026-07-16T08:30:00Z",
            last_run_status: "completed",
            lead_user_id: "admin-1",
            member_count: 4,
            name: `${longName} ${index + 1}`,
            open_review_count: 1,
            status: index === 7 ? "archived" : "active",
            test_case_count: 12,
            test_plan_count: 2,
            updated_at: "2026-07-16T08:30:00Z",
            updated_by: "admin-1",
          })),
          next_cursor: null,
        },
      });
      return;
    }
    await route.continue();
  });
  await page.route("**/api/v1/projects/*", async (route) => {
    if (route.request().method() === "PATCH") {
      const body = route.request().postDataJSON() as { name: string };
      await route.fulfill({
        contentType: "application/json",
        json: {
          active_environment_count: 1,
          agent_count: 2,
          archived: false,
          created_at: "2026-07-16T00:00:00Z",
          created_by: "admin-1",
          dataset_count: 3,
          description: "覆盖专业测试资产与执行闭环的项目",
          id: "project-0-with-a-long-stable-identifier",
          key: "MISSION-1",
          lead_user_id: "admin-1",
          member_count: 4,
          name: body.name,
          open_review_count: 1,
          status: "active",
          test_case_count: 12,
          test_plan_count: 2,
          updated_at: "2026-07-16T08:30:00Z",
          updated_by: "admin-1",
        },
      });
      return;
    }
    await route.continue();
  });
}

async function assertNoHorizontalOverflow(page: Page) {
  const measurements = await page.evaluate(() => ({
    bodyClientWidth: document.body.clientWidth,
    bodyScrollWidth: document.body.scrollWidth,
    documentClientWidth: document.documentElement.clientWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
  }));

  expect(measurements.bodyScrollWidth).toBeLessThanOrEqual(
    measurements.bodyClientWidth,
  );
  expect(measurements.documentScrollWidth).toBeLessThanOrEqual(
    measurements.documentClientWidth,
  );
}

for (const width of [1280, 1440, 1920]) {
  test(`project list fits every column at ${width}px`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ height: 900, width });
    await mockProjectList(page);
    await page.goto("/projects");

    await expect(page.getByRole("heading", { name: "项目管理" })).toBeVisible();
    await expect(
      page.getByRole("columnheader", { name: "操作" }),
    ).toBeVisible();
    await assertNoHorizontalOverflow(page);

    const firstRow = page.getByRole("row").filter({ hasText: `${longName} 1` });
    const actionGroup = firstRow.getByRole("group");
    const actionBox = await actionGroup.boundingBox();
    expect(actionBox).not.toBeNull();
    expect(actionBox!.x + actionBox!.width).toBeLessThanOrEqual(width);

    const projectName = firstRow.getByLabel(`${longName} 1`, { exact: true });
    const textMetrics = await projectName.evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
    }));
    expect(textMetrics.scrollWidth).toBeGreaterThan(textMetrics.clientWidth);

    await firstRow.getByRole("button", { name: `编辑${longName} 1` }).hover();
    const tooltip = firstRow.locator('[role="tooltip"][data-tooltip^="编辑"]');
    await expect(tooltip).toHaveCSS("opacity", "1");
    const iconMetrics = await firstRow
      .getByRole("button", { name: `编辑${longName} 1` })
      .locator("svg")
      .evaluate((icon) => {
        const box = icon.getBoundingClientRect();
        const style = getComputedStyle(icon);
        return {
          color: style.color,
          display: style.display,
          height: box.height,
          opacity: style.opacity,
          visibility: style.visibility,
          width: box.width,
        };
      });
    expect(iconMetrics).toMatchObject({
      display: "block",
      height: 16,
      opacity: "1",
      visibility: "visible",
      width: 16,
    });
    if (width === 1440) {
      await page.screenshot({
        fullPage: true,
        path: testInfo.outputPath("project-list-1440.png"),
      });
    }
  });
}

test("workspace shell supports grouped navigation, command search, and three-state themes", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ height: 900, width: 1440 });
  await mockProjectList(page);
  await page.goto("/projects");

  await expect(page.getByText("工作台", { exact: true })).toBeVisible();
  await expect(page.getByText("测试资产", { exact: true })).toBeVisible();
  await expect(page.getByText("执行中心", { exact: true })).toBeVisible();
  await expect(page.getByText("评测与治理", { exact: true })).toBeVisible();

  await page.keyboard.press("Control+K");
  const command = page.getByRole("dialog", { name: "全局搜索" });
  await expect(command).toBeVisible();
  await command.getByRole("searchbox", { name: "全局搜索" }).fill("安全");
  await expect(command.getByRole("option", { name: "安全测试" })).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(
    /\/projects\/project-0-with-a-long-stable-identifier\/security$/,
  );
  await page.goto("/projects");

  await page.getByRole("button", { name: "外观设置" }).click();
  await page.getByRole("menuitemradio", { name: "深色" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "dark",
  );
  await expect(page.getByRole("button", { name: "全部状态" })).toHaveCSS(
    "background-color",
    "rgb(31, 31, 34)",
  );
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("workspace-shell-dark-1440.png"),
  });

  await page.getByRole("button", { name: "外观设置" }).click();
  await page.getByRole("menuitemradio", { name: "跟随系统" }).click();
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "system",
  );

  const helpButton = page.getByRole("button", { name: "帮助中心" });
  await helpButton.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("menu", { name: "帮助中心" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(helpButton).toBeFocused();
});

test("theme hydration, reload, and system changes remain stable on every route", async ({
  page,
}) => {
  const hydrationErrors: string[] = [];
  page.on("console", (message) => {
    if (
      message.type() === "error" &&
      /hydration|Minified React error #418/i.test(message.text())
    ) {
      hydrationErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => {
    if (/hydration|Minified React error #418/i.test(error.message)) {
      hydrationErrors.push(error.message);
    }
  });
  await page.addInitScript(() => {
    if (!localStorage.getItem("theme")) localStorage.setItem("theme", "dark");
  });

  await page.goto("/login");
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "dark",
  );
  await page.reload();
  await expect(page.locator("html")).toHaveClass(/dark/);
  expect(hydrationErrors).toEqual([]);

  await page.evaluate(() => localStorage.setItem("theme", "system"));
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/docs");
  await expect(page.locator("html")).toHaveClass(/light/);
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "system",
  );
  expect(hydrationErrors).toEqual([]);
});

test("quick create opens and reopens the existing form from its target list", async ({
  page,
}) => {
  const projectId = "project-0-with-a-long-stable-identifier";
  await mockProjectList(page);
  await page.route(
    `**/api/v1/projects/${projectId}/datasets**`,
    async (route) => {
      await route.fulfill({
        contentType: "application/json",
        json: { items: [], next_cursor: null },
      });
    },
  );
  await page.goto(`/projects/${projectId}/datasets`);
  await expect(page.getByRole("heading", { name: "测试用例" })).toBeVisible();

  for (let attempt = 0; attempt < 2; attempt += 1) {
    await page.getByRole("button", { name: "快速创建" }).click();
    await page.getByRole("menuitem", { name: "用例集" }).click();
    const dialog = page.getByRole("dialog", { name: "创建用例集" });
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "关闭" }).click();
    await expect(dialog).toBeHidden();
    await expect(page).not.toHaveURL(/create=dataset/);
  }
});

test("project edit uses a dialog and narrow screens never scroll sideways", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ height: 844, width: 390 });
  await mockProjectList(page);
  await page.goto("/projects");

  await assertNoHorizontalOverflow(page);
  await page.getByRole("button", { name: "打开导航" }).click();
  const navigation = page.getByRole("dialog", { name: "项目导航" });
  await expect(navigation).toBeVisible();
  await expect(
    navigation.getByRole("link", { name: "测试 Agent" }),
  ).toBeVisible();
  await navigation.getByRole("button", { name: "关闭导航" }).click();
  const edit = page.getByRole("button", { name: `编辑${longName} 1` });
  await expect(edit).toBeVisible();
  await edit.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "编辑项目" })).toBeVisible();
  const nameInput = dialog.getByRole("textbox", { name: "项目名称" });
  await expect(nameInput).toHaveValue(`${longName} 1`);
  await nameInput.fill("移动端编辑后的项目名称");
  await page.getByRole("button", { name: "保存修改" }).click();
  await expect(page.getByRole("heading", { name: "编辑项目" })).toBeHidden();
  await assertNoHorizontalOverflow(page);
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("project-list-390.png"),
  });
});
