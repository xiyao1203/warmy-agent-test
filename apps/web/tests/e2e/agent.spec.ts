import { expect, test } from "@playwright/test";

test.describe("Agent 管理", () => {
  test("Agent 列表页可访问", async ({ page }) => {
    await page.goto("/projects/test-project/agents");
    // 页面应该加载（可能需要登录）
    await expect(page.locator("h1, h2, h3").first()).toBeVisible({ timeout: 5000 });
  });
});
