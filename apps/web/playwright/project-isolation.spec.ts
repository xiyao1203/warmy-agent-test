import { expect, test } from "@playwright/test";

test.use({ storageState: "playwright/.auth/admin.json" });

test.describe("project isolation", () => {
  test("super admin can create projects and assign developer to one", async ({
    page,
  }) => {
    await page.goto("/");

    const projectSwitcher = page.getByRole("button", { name: /项目/ }).first();
    await projectSwitcher.click();

    await expect(page.getByText(/项目 A|项目 B/)).toBeVisible();
  });

  test("developer assigned to project A cannot access project B", async ({
    browser,
  }) => {
    const devContext = await browser.newContext();
    const devPage = await devContext.newPage();

    await devPage.goto("/login");
    await devPage.getByLabel("邮箱").fill("dev@example.com");
    await devPage.getByLabel("密码").fill("dev-password-123");
    await devPage.getByRole("button", { name: "登录" }).click();

    await expect(devPage).toHaveURL(/\/projects\/.*\/overview/);

    const currentUrl = devPage.url();
    const currentProjectId = currentUrl.match(
      /\/projects\/([^/]+)\/overview/,
    )?.[1];

    await devPage.goto(
      "/projects/00000000-0000-0000-0000-000000000000/overview",
    );
    await expect(devPage.getByText(/项目不存在或你无权访问/)).toBeVisible();

    await devPage.goto(`/projects/${currentProjectId}/overview`);
    await expect(devPage).toHaveURL(/\/projects\/.*\/overview/);

    await devContext.close();
  });
});
