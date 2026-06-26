import { expect, test } from "@playwright/test";

test.describe("数据集管理", () => {
  test("数据集列表页可访问", async ({ page }) => {
    await page.goto("/projects/test-project/datasets");
    await expect(page.locator("h1, h2, h3").first()).toBeVisible({ timeout: 5000 });
  });
});
