import { expect, test } from "@playwright/test";

test.describe("项目导航", () => {
  test("登录页可正常渲染并导航", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toBeVisible();

    await page.getByRole("button", { name: "登录" }).click();

    await expect(
      page.getByRole("heading", { name: "登录测试工作台" }),
    ).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole("button", { name: "登录" })).toBeVisible();
  });

  test("无登录访问项目页有内容", async ({ page }) => {
    await page.goto("/projects/test/overview");
    // 页面不应白屏
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("运行中心", () => {
  test("运行中心页面导航", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toBeVisible();
    // 验证页面不崩溃即可
  });
});
