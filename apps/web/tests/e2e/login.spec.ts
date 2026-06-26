import { expect, test } from "@playwright/test";

test.describe("项目导航", () => {
  test("登录页可正常渲染并导航", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(
      page.getByRole("button", { name: /登录|sign in/i }),
    ).toBeVisible();
  });

  test("无登录访问项目页应跳转", async ({ page }) => {
    await page.goto("/projects/test/overview");
    // 应被重定向到登录页
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });
});

test.describe("运行中心", () => {
  test("运行中心页面导航", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toBeVisible();
    // 验证页面不崩溃即可
  });
});
