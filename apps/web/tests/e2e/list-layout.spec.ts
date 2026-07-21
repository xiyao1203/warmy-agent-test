import { expect, test, type Page } from "@playwright/test";
import type { Locator } from "@playwright/test";

const longName =
  "Mission Acceptance 超长项目名称用于验证列表一屏显示、文本完整提示能力以及极端用户输入不会撑破操作列的稳定布局";
const resourceProjectId = "project-0-with-a-long-stable-identifier";

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
  await page.route("**/api/v1/projects**", async (route) => {
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
          page: 1,
          page_size: 10,
          total: 8,
          total_pages: 1,
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

async function mockResourceLists(page: Page) {
  await mockProjectList(page);
  await page.route(
    `**/api/v1/projects/${resourceProjectId}/**`,
    async (route) => {
      const path = new URL(route.request().url()).pathname;

      if (path === `/api/v1/projects/${resourceProjectId}/agents`) {
        await route.fulfill({
          contentType: "application/json",
          json: {
            items: [
              {
                agent_type: "generic_http",
                baseline_version_id: "agent-version-2",
                connection_status: "ready",
                created_at: "2026-07-16T00:00:00Z",
                created_by: "admin-1",
                credential_binding_count: 2,
                current_version: {
                  href: `/projects/${resourceProjectId}/agents/agent-1`,
                  id: "agent-version-2",
                  name: "客服测试 Agent",
                  resource_type: "agent_version",
                  status: "published",
                  version: 2,
                },
                current_version_id: "agent-version-2",
                description: "覆盖多轮客服问答与工具调用的自动化测试 Agent",
                id: "agent-1",
                last_run_status: "passed",
                model: "glm-4.5",
                name: "客服测试 Agent",
                pass_rate: 0.96,
                project_id: resourceProjectId,
                protocol: "responses",
                tool_count: 4,
                updated_at: "2026-07-16T08:30:00Z",
                updated_by: "admin-1",
              },
            ],
            next_cursor: null,
            page: 1,
            page_size: 10,
            total: 1,
            total_pages: 1,
          },
        });
        return;
      }

      if (path === `/api/v1/projects/${resourceProjectId}/datasets`) {
        await route.fulfill({
          contentType: "application/json",
          json: {
            items: [
              {
                api_count: 12,
                browser_count: 5,
                case_count: 20,
                codex_explore_count: 3,
                created_at: "2026-07-16T00:00:00Z",
                created_by: "admin-1",
                description: "Agent 对话回归集",
                id: "dataset-1",
                latest_version: {
                  href: `/projects/${resourceProjectId}/datasets/dataset-1`,
                  id: "dataset-version-3",
                  name: "对话回归",
                  resource_type: "dataset_version",
                  status: "published",
                  version: 3,
                },
                name: "对话回归",
                priority_coverage: { P0: 4, P1: 16 },
                project_id: resourceProjectId,
                ready_count: 18,
                source_distribution: { agent_generated: 8, manual: 12 },
                updated_at: "2026-07-16T08:30:00Z",
                updated_by: "admin-1",
              },
            ],
            next_cursor: null,
            page: 1,
            page_size: 10,
            total: 1,
            total_pages: 1,
          },
        });
        return;
      }

      if (path === `/api/v1/projects/${resourceProjectId}/test-plans`) {
        await route.fulfill({
          contentType: "application/json",
          json: {
            items: [
              {
                agent_ref: {
                  href: `/projects/${resourceProjectId}/agents/agent-1`,
                  id: "agent-version-2",
                  name: "客服测试 Agent",
                  resource_type: "agent_version",
                  version: 2,
                },
                case_count: 48,
                concurrency: 4,
                created_at: "2026-07-16T00:00:00Z",
                created_by: "admin-1",
                dataset_ref: {
                  href: `/projects/${resourceProjectId}/datasets/dataset-1`,
                  id: "dataset-version-3",
                  name: "对话回归",
                  resource_type: "dataset_version",
                  version: 3,
                },
                description: "覆盖发布门禁的核心回归计划",
                environment_ref: {
                  href: `/projects/${resourceProjectId}/environments`,
                  id: "environment-1",
                  name: "预发环境",
                  resource_type: "environment",
                },
                id: "plan-1",
                last_run_status: "passed",
                latest_version: {
                  href: `/projects/${resourceProjectId}/test-plans/plan-1`,
                  id: "plan-version-4",
                  name: "回归计划",
                  resource_type: "test_plan_version",
                  status: "published",
                  version: 4,
                },
                name: "回归计划",
                pass_rate: 0.96,
                project_id: resourceProjectId,
                repeat_count: 2,
                retry_count: 1,
                scorer_count: 3,
                timeout_seconds: 120,
                updated_at: "2026-07-16T08:30:00Z",
                updated_by: "admin-1",
              },
            ],
            next_cursor: null,
            page: 1,
            page_size: 10,
            total: 1,
            total_pages: 1,
          },
        });
        return;
      }

      if (
        path ===
        `/api/v1/projects/${resourceProjectId}/test-plans/plan-1/versions`
      ) {
        await route.fulfill({
          contentType: "application/json",
          json: {
            items: [
              {
                created_at: "2026-07-16T00:00:00Z",
                created_by: "admin-1",
                id: "plan-version-4",
                published_at: "2026-07-16T01:00:00Z",
                status: "published",
                test_plan_id: "plan-1",
                updated_at: "2026-07-16T01:00:00Z",
                version_number: 4,
              },
            ],
          },
        });
        return;
      }

      if (path === `/api/v1/projects/${resourceProjectId}/runs`) {
        await route.fulfill({
          contentType: "application/json",
          json: {
            items: [
              {
                agent_ref: {
                  href: `/projects/${resourceProjectId}/agents/agent-1`,
                  id: "agent-version-2",
                  name: "客服测试 Agent",
                  resource_type: "agent_version",
                  version: 2,
                },
                cancelled_cases: 0,
                completed_at: "2026-07-16T08:31:00Z",
                cost: 0.0245,
                created_at: "2026-07-16T08:30:00Z",
                created_by_ref: {
                  id: "admin-1",
                  name: "Admin",
                  resource_type: "user",
                },
                dataset_ref: {
                  href: `/projects/${resourceProjectId}/datasets/dataset-1`,
                  id: "dataset-version-3",
                  name: "对话回归",
                  resource_type: "dataset_version",
                  version: 3,
                },
                duration_ms: 5600,
                error_cases: 0,
                failed_cases: 0,
                id: "run-1",
                passed_cases: 48,
                plan_ref: {
                  href: `/projects/${resourceProjectId}/test-plans/plan-1`,
                  id: "plan-version-4",
                  name: "回归计划",
                  resource_type: "test_plan_version",
                  version: 4,
                },
                progress: 1,
                project_id: resourceProjectId,
                run_number: "RUN-9001",
                run_type: "plan",
                source_test_case_id: null,
                started_at: "2026-07-16T08:30:01Z",
                status: "passed",
                test_plan_version_id: "plan-version-4",
                token_usage: { total: 2048 },
                total_cases: 48,
                trigger_type: "manual",
                workflow_id: "workflow-run-9001",
              },
            ],
            next_cursor: null,
            page: 1,
            page_size: 10,
            total: 1,
            total_pages: 1,
          },
        });
        return;
      }

      await route.continue();
    },
  );
}

async function assertAdaptiveResourceTable(
  page: Page,
  options: {
    actionName: string;
    heading: string;
    path: string;
    rowText: string;
    tooltip: string;
  },
) {
  await page.goto(options.path);
  await expect(
    page.getByRole("heading", { name: options.heading }),
  ).toBeVisible();

  const table = page.getByRole("table");
  const row = table.getByRole("row").filter({ hasText: options.rowText });
  await expect(row).toBeVisible();

  await assertRowCenterAlignment(row);

  const actionGroup = row.getByRole("group");
  const actionGeometry = await actionGroup.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return {
      display: getComputedStyle(element).display,
      height: rect.height,
      right: rect.right,
      whiteSpace: getComputedStyle(element).whiteSpace,
    };
  });
  expect(actionGeometry).toMatchObject({
    display: "inline-flex",
    whiteSpace: "nowrap",
  });
  expect(actionGeometry.height).toBeLessThanOrEqual(36);
  expect(actionGeometry.right).toBeLessThanOrEqual(page.viewportSize()!.width);

  await row.getByRole("link", { name: options.actionName }).hover();
  const tooltip = row.locator(
    `[role="tooltip"][data-tooltip="${options.tooltip}"]`,
  );
  await expect(tooltip).toHaveCSS("opacity", "1");
  const tooltipBox = await tooltip.boundingBox();
  expect(tooltipBox).not.toBeNull();
  expect(tooltipBox!.height).toBeLessThanOrEqual(30);
  await assertNoHorizontalOverflow(page);
}

async function assertRowCenterAlignment(row: Locator) {
  const alignment = await row.evaluate((rowElement) => {
    const headers = Array.from(
      rowElement.closest("table")?.querySelectorAll("thead th") ?? [],
    );
    const cells = Array.from(rowElement.querySelectorAll("td"));
    return cells.map((cell, index) => {
      const header = headers[index];
      const content =
        Array.from(cell.children).find((element) => {
          const rect = element.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        }) ?? cell;
      const headerRect = header.getBoundingClientRect();
      const contentRect = content.getBoundingClientRect();
      return Math.abs(
        headerRect.left +
          headerRect.width / 2 -
          (contentRect.left + contentRect.width / 2),
      );
    });
  });
  expect(alignment.length).toBeGreaterThan(0);
  for (const centerDelta of alignment)
    expect(centerDelta).toBeLessThanOrEqual(4);
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
    await assertRowCenterAlignment(firstRow);
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

test("developer typography stays consistent across themes and mobile", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ height: 900, width: 1440 });
  await page.addInitScript(() => localStorage.setItem("theme", "light"));
  await mockProjectList(page);
  await page.goto("/projects");

  const title = page.getByRole("heading", { name: "项目管理", level: 1 });
  const description = page.getByText(
    "管理测试资产所在项目，进入项目后默认打开测试 Agent。",
  );
  const createButton = page.getByRole("button", { name: "新建项目" });
  const firstHeader = page.getByRole("columnheader", { name: "项目" });
  const firstCell = page.getByRole("cell").first();

  await expect(page.locator("html")).toHaveCSS("font-family", /Geist/i);
  await expect(title).toHaveCSS("font-size", "26px");
  await expect(title).toHaveCSS("font-weight", "600");
  await expect(title).toHaveCSS("line-height", "36px");
  await expect(title).toHaveCSS("letter-spacing", "-0.52px");
  await expect(title).toHaveCSS("color", "rgb(16, 24, 40)");
  await expect(description).toHaveCSS("font-size", "14px");
  await expect(description).toHaveCSS("line-height", "22px");
  await expect(description).toHaveCSS("color", "rgb(71, 84, 103)");
  await expect(createButton).toHaveCSS("font-size", "14px");
  await expect(createButton).toHaveCSS("font-weight", "600");
  await expect(firstHeader).toHaveCSS("font-size", "13px");
  await expect(firstHeader).toHaveCSS("font-weight", "500");
  await expect(firstHeader).toHaveCSS("line-height", "20px");
  await expect(firstCell).toHaveCSS("font-size", "14px");
  await expect(firstCell).toHaveCSS("font-weight", "400");
  await expect(firstCell).toHaveCSS("line-height", "22px");

  const navigationLabel = page.getByText("工作台", { exact: true });
  const navigationLink = page.getByRole("link", { name: "项目列表" });
  await expect(navigationLabel).toHaveCSS("font-size", "12px");
  await expect(navigationLabel).toHaveCSS("font-weight", "500");
  await expect(navigationLink).toHaveCSS("font-size", "14px");
  await expect(navigationLink).toHaveCSS("font-weight", "600");
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("developer-typography-light-1440.png"),
  });

  await page.getByRole("button", { name: "切换至深色" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(title).toHaveCSS("color", "rgb(245, 247, 250)");
  await expect(description).toHaveCSS("color", "rgb(152, 162, 179)");
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("developer-typography-dark-1440.png"),
  });

  await page.setViewportSize({ height: 844, width: 390 });
  await assertNoHorizontalOverflow(page);
  const [titleBox, buttonBox] = await Promise.all([
    title.boundingBox(),
    createButton.boundingBox(),
  ]);
  expect(titleBox).not.toBeNull();
  expect(buttonBox).not.toBeNull();
  expect(titleBox!.x + titleBox!.width).toBeLessThanOrEqual(390);
  expect(buttonBox!.x + buttonBox!.width).toBeLessThanOrEqual(390);
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("developer-typography-dark-390.png"),
  });
  await page.getByRole("button", { name: "切换至浅色" }).click();
  await expect(page.locator("html")).toHaveClass(/light/);
  await expect(page.getByRole("button", { name: "全部状态" })).toHaveCSS(
    "background-color",
    "rgb(255, 255, 255)",
  );
  await assertNoHorizontalOverflow(page);
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("developer-typography-light-390.png"),
  });
});

const adaptiveResourcePages = [
  {
    actionName: "管理客服测试 Agent",
    heading: "Agent 与版本",
    path: `/projects/${resourceProjectId}/agents`,
    rowText: "客服测试 Agent",
    tooltip: "管理",
  },
  {
    actionName: "管理对话回归用例",
    heading: "测试用例",
    path: `/projects/${resourceProjectId}/datasets`,
    rowText: "对话回归",
    tooltip: "管理",
  },
  {
    actionName: "配置回归计划",
    heading: "测试计划",
    path: `/projects/${resourceProjectId}/test-plans`,
    rowText: "回归计划",
    tooltip: "配置",
  },
  {
    actionName: "查看运行 run-1 结果",
    heading: "运行中心",
    path: `/projects/${resourceProjectId}/runs`,
    rowText: "RUN-9001",
    tooltip: "查看",
  },
] as const;

for (const width of [1280, 1440, 1920]) {
  test(`core resource tables stay centered and actionable at ${width}px`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ height: 900, width });
    await mockResourceLists(page);

    for (const resourcePage of adaptiveResourcePages) {
      await assertAdaptiveResourceTable(page, resourcePage);
    }

    if (width === 1440) {
      await page.screenshot({
        fullPage: true,
        path: testInfo.outputPath("run-list-1440.png"),
      });
    }
  });
}

test("workspace shell supports grouped navigation, command search, and two-state themes", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ height: 900, width: 1440 });
  await page.addInitScript(() => localStorage.setItem("theme", "light"));
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

  const darkToggle = page.getByRole("button", { name: "切换至深色" });
  await darkToggle.hover();
  await expect(
    page.locator('[role="tooltip"][data-tooltip="切换至深色"]'),
  ).toBeVisible();
  await page.locator("header.app-topbar").screenshot({
    path: testInfo.outputPath("theme-toggle-light-header-1440.png"),
  });
  await darkToggle.click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "dark",
  );
  const lightToggle = page.getByRole("button", { name: "切换至浅色" });
  const lightTooltip = page.locator(
    '[role="tooltip"][data-tooltip="切换至浅色"]',
  );
  await expect(lightToggle).toBeFocused();
  await expect(lightTooltip).toHaveCSS("opacity", "0");
  await page.mouse.move(10, 400);
  await expect(lightTooltip).toHaveCSS("opacity", "0");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Shift+Tab");
  await expect(lightToggle).toBeFocused();
  await expect(lightTooltip).toHaveCSS("opacity", "1");
  await page.keyboard.press("Tab");
  await expect(lightTooltip).toHaveCSS("opacity", "0");
  await expect(page.getByRole("button", { name: "全部状态" })).toHaveCSS(
    "background-color",
    "rgb(31, 31, 34)",
  );
  await page.getByRole("button", { name: "全局搜索" }).click();
  const darkCommand = page.getByRole("dialog", { name: "全局搜索" });
  const darkCommandSearch = darkCommand.getByRole("searchbox", {
    name: "全局搜索",
  });
  await expect(darkCommandSearch).toHaveCSS("border-top-width", "0px");
  await expect(darkCommandSearch).toHaveCSS("border-right-width", "0px");
  await expect(darkCommandSearch).toHaveCSS("border-bottom-width", "0px");
  await expect(darkCommandSearch).toHaveCSS("border-left-width", "0px");
  await expect(darkCommandSearch).toHaveCSS("outline-style", "none");
  await expect(darkCommandSearch).toHaveCSS("box-shadow", "none");
  await darkCommand.screenshot({
    path: testInfo.outputPath("command-search-dark-borderless.png"),
  });
  await page.keyboard.press("Escape");
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("workspace-shell-dark-1440.png"),
  });
  await page.locator("header.app-topbar").screenshot({
    path: testInfo.outputPath("theme-toggle-dark-header-1440.png"),
  });

  await expect(page.getByRole("menuitemradio")).toHaveCount(0);
  await lightToggle.click();
  await expect(page.locator("html")).toHaveClass(/light/);
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "light",
  );

  const helpButton = page.getByRole("button", { name: "帮助中心" });
  await helpButton.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("menu", { name: "帮助中心" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(helpButton).toBeFocused();
});

test("chromatic sidebar keeps active color and collapsed hover text", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ height: 900, width: 1440 });
  await page.addInitScript(() => {
    localStorage.setItem("sidebar-collapsed", "false");
    localStorage.setItem("theme", "light");
  });
  await mockResourceLists(page);
  await page.goto(`/projects/${resourceProjectId}/datasets`);

  const datasetLink = page.getByRole("link", { name: "测试用例" });
  await expect(datasetLink).toHaveAttribute("aria-current", "page");
  await expect(datasetLink).toHaveAttribute("data-navigation-tone", "indigo");
  await expect(
    datasetLink.locator('[data-navigation-icon="chromatic-signal"]'),
  ).toBeVisible();
  await expect(datasetLink.locator("[data-navigation-signal]")).toBeVisible();
  await page.locator("aside.app-sidebar").screenshot({
    path: testInfo.outputPath("chromatic-sidebar-light-expanded.png"),
  });

  await page.getByRole("button", { name: "收起侧边栏" }).click();
  await expect(page.locator("aside.app-sidebar")).toHaveAttribute(
    "data-collapsed",
    "true",
  );
  await expect(page.locator("aside.app-sidebar")).toHaveCSS("width", "56px");
  await datasetLink.hover();
  const navigationTooltip = page.locator(
    '[role="tooltip"][data-tooltip="测试用例"]',
  );
  await expect(navigationTooltip).toBeVisible();
  await expect(navigationTooltip).toHaveAttribute("data-state", "open");
  await expect(navigationTooltip).toHaveCSS("opacity", "1");
  await expect(navigationTooltip).toHaveCSS("z-index", "80");
  expect(
    await navigationTooltip.evaluate(
      (element) => element.parentElement === document.body,
    ),
  ).toBe(true);
  const [sidebarBox, tooltipBox] = await Promise.all([
    page.locator("aside.app-sidebar").boundingBox(),
    navigationTooltip.boundingBox(),
  ]);
  expect(sidebarBox).not.toBeNull();
  expect(tooltipBox).not.toBeNull();
  expect(tooltipBox!.x).toBeGreaterThanOrEqual(
    sidebarBox!.x + sidebarBox!.width - 1,
  );
  await page.screenshot({
    path: testInfo.outputPath("chromatic-sidebar-light-collapsed.png"),
  });

  await page.mouse.move(900, 500);
  const searchTrigger = page.getByRole("button", { name: "全局搜索" });
  await expect(searchTrigger).toHaveCSS("border-top-width", "0px");
  await expect(searchTrigger).toHaveCSS("border-right-width", "0px");
  await expect(searchTrigger).toHaveCSS("border-bottom-width", "0px");
  await expect(searchTrigger).toHaveCSS("border-left-width", "0px");
  await searchTrigger.click();
  const commandSearch = page.getByRole("searchbox", { name: "全局搜索" });
  const commandSearchRegion = page.locator(".app-command-search");
  await expect(commandSearchRegion).toHaveCSS("border-top-width", "0px");
  await expect(commandSearchRegion).toHaveCSS("border-right-width", "0px");
  await expect(commandSearchRegion).toHaveCSS("border-bottom-width", "0px");
  await expect(commandSearchRegion).toHaveCSS("border-left-width", "0px");
  await expect(commandSearch).toHaveCSS("outline-style", "none");
  await expect(commandSearch).toHaveCSS("box-shadow", "none");
  await page.getByRole("dialog", { name: "全局搜索" }).screenshot({
    path: testInfo.outputPath("command-search-borderless.png"),
  });
  await page.keyboard.press("Escape");

  await page.getByRole("button", { name: "切换至深色" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await page.mouse.move(900, 500);
  await page.locator("aside.app-sidebar").screenshot({
    path: testInfo.outputPath("chromatic-sidebar-dark-collapsed.png"),
  });

  await page.getByRole("button", { name: "展开侧边栏" }).click();
  await expect(page.locator("aside.app-sidebar")).toHaveAttribute(
    "data-collapsed",
    "false",
  );

  await page.setViewportSize({ height: 844, width: 390 });
  await page.getByRole("button", { name: "打开导航" }).click();
  const mobileNavigation = page.getByRole("dialog", { name: "项目导航" });
  await expect(
    mobileNavigation
      .getByRole("link", { name: "测试用例" })
      .locator('[data-navigation-icon="chromatic-signal"]'),
  ).toBeVisible();
  await mobileNavigation.screenshot({
    path: testInfo.outputPath("chromatic-sidebar-mobile-dark.png"),
  });
  await mobileNavigation.getByRole("button", { name: "关闭导航" }).click();

  await page.getByRole("button", { name: "切换至浅色" }).click();
  await page.getByRole("button", { name: "打开导航" }).click();
  await mobileNavigation.screenshot({
    path: testInfo.outputPath("chromatic-sidebar-mobile-light.png"),
  });
  await expect(page.locator("html")).toHaveClass(/light/);
});

test("theme hydration, reload, and legacy migration remain stable on every route", async ({
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

  await page.emulateMedia({ colorScheme: "dark" });
  await page.evaluate(() => localStorage.setItem("theme", "system"));
  await page.goto("/docs");
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "dark",
  );
  await expect
    .poll(() => page.evaluate(() => localStorage.getItem("theme")))
    .toBe("dark");
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme-preference",
    "dark",
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
        json: {
          items: [],
          next_cursor: null,
          page: 1,
          page_size: 10,
          total: 0,
          total_pages: 0,
        },
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
