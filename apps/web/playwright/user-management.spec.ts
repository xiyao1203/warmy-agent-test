import { expect, test } from "@playwright/test";

test.use({ storageState: "playwright/.auth/admin.json" });

test.describe("user management", () => {
  test("super admin can create a developer", async ({ page }) => {
    await page.goto("/system/users");

    await expect(page.getByRole("heading", { name: "用户管理" })).toBeVisible();

    await page.getByRole("button", { name: "创建用户" }).click();

    const unique = Date.now().toString(36);
    await page.getByLabel("姓名").fill(`E2E开发者${unique}`);
    await page.getByLabel("邮箱").fill(`e2e-dev-${unique}@example.com`);
    await page.getByLabel("初始密码").fill("Secure-e2e-password-123");
    await page.getByLabel("系统角色").selectOption("developer");

    await page.getByRole("button", { name: "保存用户" }).click();

    await expect(page.getByText(`e2e-dev-${unique}@example.com`)).toBeVisible();
  });

  test("developer cannot access user management", async ({ browser }) => {
    const devContext = await browser.newContext();
    const page = await devContext.newPage();

    await page.goto("/login");
    await page.getByLabel("邮箱").fill("dev@example.com");
    await page.getByLabel("密码").fill("dev-password-123");
    await page.getByRole("button", { name: "登录" }).click();

    await page.goto("/system/users");
    await expect(page.getByText(/没有用户管理权限/)).toBeVisible();

    await devContext.close();
  });

  test("disabling a user invalidates their session", async ({ browser }) => {
    const devContext = await browser.newContext();
    const devPage = await devContext.newPage();

    await devPage.goto("/login");
    await devPage.getByLabel("邮箱").fill("dev2@example.com");
    await devPage.getByLabel("密码").fill("dev2-password-123");
    await devPage.getByRole("button", { name: "登录" }).click();

    await expect(devPage).toHaveURL(/\/projects\/.*\/overview/);

    const adminPage = await browser.newPage();
    await adminPage.goto("/system/users");
    await adminPage.getByRole("button", { name: /查看.*dev2/ }).click();
    await adminPage.getByRole("button", { name: "禁用用户" }).click();
    await adminPage.getByRole("button", { name: "确认禁用用户" }).click();

    await devPage.reload();
    await expect(devPage).toHaveURL(/\/login/);

    await devContext.close();
  });

  test("last active super admin cannot be disabled", async ({ page }) => {
    await page.goto("/system/users");

    const adminRow = page.locator("tr", { hasText: "admin@example.com" });
    await adminRow.getByRole("button", { name: /查看/ }).click();

    await expect(
      page.getByText(/当前账号不能在此禁用或降权/),
    ).toBeVisible();
    await expect(
      page.queryByRole("button", { name: "禁用用户" }),
    ).not.toBeVisible();
  });
});
