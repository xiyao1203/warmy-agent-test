import { expect, test } from "@playwright/test";

test.describe("测试计划管理", () => {
  test("测试计划列表页可访问", async ({ page }) => {
    await page.goto("/projects/test-project/test-plans");
    await expect(page.locator("h1, h2, h3").first()).toBeVisible({ timeout: 5000 });
  });
});
