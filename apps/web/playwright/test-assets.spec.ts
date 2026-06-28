import { expect, test } from "@playwright/test";
import type { Page, Browser } from "@playwright/test";

// 使用预认证的管理员状态，避免重复登录
test.use({ storageState: "playwright/.auth/admin.json" });

test.describe("test assets E2E", () => {
  const projectId = process.env.E2E_PROJECT_ID ?? "";

  test.beforeAll(async ({ browser }: { browser: Browser }) => {
    // 确保存在可用项目；如果未通过环境变量指定，先创建一个
    if (!projectId) {
      const page: Page = await browser.newPage();
      await page.goto("/");
      // 如果被重定向到项目概览，则提取 projectId
      const match = page.url().match(/\/projects\/([^/]+)/);
      if (match) {
        process.env.E2E_PROJECT_ID = match[1];
      }
      await page.close();
    }
  });

  // ── 场景 1：创建 Agent 并发布版本 ─────────────────────────────────────
  test("developer creates an Agent and publishes a version", async ({ page }: { page: Page }) => {
    const pid = process.env.E2E_PROJECT_ID!;
    await page.goto(`/projects/${pid}/agents`);

    // 等待列表加载
    await expect(page.getByRole("heading")).toBeVisible();

    // 点击创建 Agent
    await page.getByRole("button", { name: /创建|新建/ }).first().click();

    const unique = Date.now().toString(36);
    await page.getByLabel(/名称/).fill(`E2E-Agent-${unique}`);
    await page.getByLabel(/类型/).selectOption("generic_http");
    await page.getByRole("button", { name: /保存|创建/ }).click();

    // 等待跳转到详情页
    await expect(page.getByText(`E2E-Agent-${unique}`)).toBeVisible();

    // 创建版本
    await page.getByRole("button", { name: /创建版本|新建版本/ }).click();
    await page.getByLabel(/API.*URL|api_url/i).fill("https://e2e-agent.example.com/v1");
    await page.getByLabel(/模型/).fill("gpt-4");
    await page.getByRole("button", { name: /保存/ }).click();

    // 发布版本
    await page.getByRole("button", { name: /发布/ }).click();
    // 确认发布弹窗
    await page.getByRole("button", { name: /确认发布|确认/ }).click();

    // 验证已发布状态
    await expect(page.getByText(/已发布|published/i)).toBeVisible();
    // 发布后不应有编辑按钮
    await expect(page.getByRole("button", { name: /编辑版本/ })).not.toBeVisible();
  });

  // ── 场景 2：创建 Dataset、导入用例并发布 ──────────────────────────────
  test("developer creates a Dataset, imports test cases, and publishes", async ({ page }: { page: Page }) => {
    const pid = process.env.E2E_PROJECT_ID!;
    await page.goto(`/projects/${pid}/datasets`);

    await page.getByRole("button", { name: /创建|新建/ }).first().click();

    const unique = Date.now().toString(36);
    await page.getByLabel(/名称/).fill(`E2E-Dataset-${unique}`);
    await page.getByRole("button", { name: /保存|创建/ }).click();

    await expect(page.getByText(`E2E-Dataset-${unique}`)).toBeVisible();

    // 创建版本
    await page.getByRole("button", { name: /创建版本|新建版本/ }).click();
    await page.getByRole("button", { name: /保存/ }).click();

    // 导入测试用例（JSON 格式）
    await page.getByRole("button", { name: /导入/ }).click();
    const importJson = JSON.stringify([
      {
        name: "E2E Test Case 1",
        input: { prompt: "Hello" },
        execution_mode: "api",
        assertions: [{ type: "contains", value: "world" }],
        tags: ["e2e", "smoke"],
        priority: "P1",
      },
      {
        name: "E2E Test Case 2",
        input: { prompt: "What is 2+2?" },
        execution_mode: "api",
        assertions: [{ type: "contains", value: "4" }],
        tags: ["e2e"],
        priority: "P2",
      },
    ]);
    await page.getByLabel(/格式/).selectOption("json");
    await page.getByRole("textbox", { name: /内容/ }).fill(importJson);
    await page.getByRole("button", { name: /确认导入/ }).click();

    // 验证导入的用例出现在列表中
    await expect(page.getByText("E2E Test Case 1")).toBeVisible();
    await expect(page.getByText("E2E Test Case 2")).toBeVisible();

    // 发布
    await page.getByRole("button", { name: /发布/ }).click();
    await page.getByRole("button", { name: /确认/ }).click();
    await expect(page.getByText(/已发布|published/i)).toBeVisible();
  });

  // ── 场景 3：创建 TestPlan 引用已发布版本 ──────────────────────────────
  test("developer creates a TestPlan referencing published Agent and Dataset", async ({ page }: { page: Page }) => {
    const pid = process.env.E2E_PROJECT_ID!;
    await page.goto(`/projects/${pid}/test-plans`);

    await page.getByRole("button", { name: /创建|新建/ }).first().click();

    const unique = Date.now().toString(36);
    await page.getByLabel(/名称/).fill(`E2E-Plan-${unique}`);
    await page.getByRole("button", { name: /保存|创建/ }).click();

    await expect(page.getByText(`E2E-Plan-${unique}`)).toBeVisible();

    // 创建版本
    await page.getByRole("button", { name: /创建版本|新建版本/ }).click();

    // 选择已发布的 Agent 和 Dataset 版本
    await page.getByLabel(/Agent.*版本/).selectOption({ index: 0 });
    await page.getByLabel(/Dataset.*版本/).selectOption({ index: 0 });
    await page.getByLabel(/运行次数/).fill("3");
    await page.getByLabel(/并发/).fill("2");
    await page.getByRole("button", { name: /保存/ }).click();

    // 发布
    await page.getByRole("button", { name: /发布/ }).click();
    await page.getByRole("button", { name: /确认/ }).click();
    await expect(page.getByText(/已发布|published/i)).toBeVisible();
  });

  // ── 场景 4：Viewer 可以查看但不能编辑 ─────────────────────────────────
  test("viewer can view but not edit test assets", async ({ browser }: { browser: Browser }) => {
    const viewerCtx = await browser.newContext();
    const page = await viewerCtx.newPage();

    // 使用 viewer 账号登录
    await page.goto("/login");
    await page.getByLabel("邮箱").fill("viewer@example.com");
    await page.getByLabel("密码").fill("viewer-password-123");
    await page.getByRole("button", { name: "登录" }).click();

    const pid = process.env.E2E_PROJECT_ID!;
    await page.goto(`/projects/${pid}/agents`);

    // Viewer 可以看到列表
    await expect(page.getByRole("heading")).toBeVisible();
    // 但不应该有创建按钮
    await expect(page.getByRole("button", { name: /创建|新建/ })).not.toBeVisible();

    await viewerCtx.close();
  });

  // ── 场景 5：非项目成员访问返回 404 ────────────────────────────────────
  test("non-member gets 404 on project test assets", async ({ browser }: { browser: Browser }) => {
    const outsiderCtx = await browser.newContext();
    const page = await outsiderCtx.newPage();

    // 使用未分配项目的用户登录
    await page.goto("/login");
    await page.getByLabel("邮箱").fill("outsider@example.com");
    await page.getByLabel("密码").fill("outsider-password-123");
    await page.getByRole("button", { name: "登录" }).click();

    // 尝试访问其他项目的页面
    const pid = process.env.E2E_PROJECT_ID!;
    await page.goto(`/projects/${pid}/agents`);

    // 应重定向回登录页或显示错误
    await expect(page).toHaveURL(/\/(login|$)/);

    await outsiderCtx.close();
  });

  // ── 场景 6：已发布版本不可编辑 ─────────────────────────────────────────
  test("published version cannot be edited", async ({ page }: { page: Page }) => {
    const pid = process.env.E2E_PROJECT_ID!;
    await page.goto(`/projects/${pid}/test-plans`);

    // 进入第一个已发布的 TestPlan 版本
    // 点击第一个 TestPlan
    const firstPlan = page.locator("a, button", { hasText: /E2E-Plan/ }).first();
    if (await firstPlan.isVisible()) {
      await firstPlan.click();
    }

    // 已发布版本不应有编辑/删除按钮
    await expect(page.getByRole("button", { name: /编辑版本/ })).not.toBeVisible();
    await expect(page.getByRole("button", { name: /删除/ })).not.toBeVisible();
  });

  // ── 场景 7：导入无效数据显示行级错误 ───────────────────────────────────
  test("import with invalid data shows line-by-line errors", async ({ page }: { page: Page }) => {
    const pid = process.env.E2E_PROJECT_ID!;
    await page.goto(`/projects/${pid}/datasets`);

    // 进入第一个 Dataset 的版本
    const firstDs = page.locator("a, button", { hasText: /E2E-Dataset/ }).first();
    if (await firstDs.isVisible()) {
      await firstDs.click();
    }

    // 创建新版本用于导入
    await page.getByRole("button", { name: /创建版本/ }).click();
    await page.getByRole("button", { name: /保存/ }).click();

    // 尝试导入含错误的数据
    await page.getByRole("button", { name: /导入/ }).click();
    await page.getByLabel(/格式/).selectOption("json");

    const badJson = JSON.stringify([
      { name: "Valid", input: { x: 1 }, execution_mode: "api" },
      { name: "", input: { x: 1 }, execution_mode: "api" },           // 空名称
      { name: "Bad Mode", input: { x: 1 }, execution_mode: "invalid" }, // 无效模式
    ]);
    await page.getByRole("textbox", { name: /内容/ }).fill(badJson);
    await page.getByRole("button", { name: /确认导入/ }).click();

    // 应显示错误信息（行号 + 原因）
    await expect(page.getByText(/错误/)).toBeVisible();
    await expect(page.getByText(/第.*行/)).toBeVisible();
  });
});
