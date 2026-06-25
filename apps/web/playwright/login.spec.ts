import { expect, test } from "@playwright/test";

test.describe("login flow", () => {
  test("redirects unauthenticated user to login", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: /登录/ })).toBeVisible();
  });

  test("shows generic error for invalid credentials", async ({ page }) => {
    await page.goto("/login");

    await page.getByLabel("邮箱").fill("nobody@example.com");
    await page.getByLabel("密码").fill("wrong-password-123");
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page.getByText(/邮箱或密码不正确/)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("super admin can log in and reach project overview", async ({ page }) => {
    const adminEmail = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
    const adminPassword = process.env.E2E_ADMIN_PASSWORD ?? "admin-password-123";

    await page.goto("/login");

    await page.getByLabel("邮箱").fill(adminEmail);
    await page.getByLabel("密码").fill(adminPassword);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page).toHaveURL(/\/projects\/.*\/overview/);
  });
});
