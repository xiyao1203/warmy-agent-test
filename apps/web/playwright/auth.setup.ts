import { test as setup, expect } from "@playwright/test";

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "admin-password-123";

setup("authenticate as super admin", async ({ page }) => {
  await page.goto("/login");

  await page.getByLabel("邮箱").fill(ADMIN_EMAIL);
  await page.getByLabel("密码").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "登录" }).click();

  await expect(page).toHaveURL(/\/projects\/.*\/overview/);

  await page.context().storageState({ path: "playwright/.auth/admin.json" });
});
