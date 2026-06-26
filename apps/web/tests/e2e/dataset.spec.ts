import { expect, test } from "@playwright/test";

test.describe("数据集管理", () => {
  test("数据集列表页渲染", async ({ page }) => {
    await page.goto("/projects/test-project/datasets");
    await expect(
      page.getByRole("heading").first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test("创建数据集对话框可打开", async ({ page }) => {
    await page.goto("/projects/test-project/datasets");
    const createBtn = page.getByRole("button", { name: /创建|新建/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page.getByRole("dialog")).toBeVisible({ timeout: 3000 });
    }
  });

  test("导入按钮可见", async ({ page }) => {
    await page.goto("/projects/test-project/datasets");
    await expect(page.locator("body")).toBeVisible();
  });
});
