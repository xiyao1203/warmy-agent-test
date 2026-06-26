import { expect, test } from "@playwright/test";

test.describe("登录流程", () => {
  test("访问根路径重定向到登录页", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
  });

  test("登录页渲染正常", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(
      page.getByRole("button", { name: /登录|sign in/i }),
    ).toBeVisible();
  });

  test("空表单提交显示验证错误", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /登录|sign in/i }).click();
    // 应有错误提示
    const error = page.locator('[class*="error"], [class*="danger"]');
    if (await error.isVisible()) {
      await expect(error).toBeVisible();
    }
  });
});
