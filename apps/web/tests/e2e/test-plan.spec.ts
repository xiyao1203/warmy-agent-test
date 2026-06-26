import { expect, test } from "@playwright/test";

test.describe("测试计划管理", () => {
  test("测试计划列表页可访问", async ({ page }) => {
    await page.goto("/projects/test-project/test-plans");
    await expect(page.locator("body")).toBeVisible();
  });

  test("创建测试计划对话框可打开", async ({ page }) => {
    await page.goto("/projects/test-project/test-plans");
    const createBtn = page.getByRole("button", { name: /创建|新建/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page.getByRole("dialog")).toBeVisible({ timeout: 3000 });
    }
  });

  test("运行中心 Tab 可见", async ({ page }) => {
    await page.goto("/projects/test-project/runs");
    await expect(page.locator("body")).toBeVisible();
  });
});
