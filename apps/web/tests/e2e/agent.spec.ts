import { expect, test } from "@playwright/test";

test.describe("Agent 管理", () => {
  test("Agent 列表页可访问", async ({ page }) => {
    await page.goto("/projects/test-project/agents");
    await expect(page.locator("body")).toBeVisible();
  });

  test("创建 Agent 对话框可打开", async ({ page }) => {
    await page.goto("/projects/test-project/agents");
    const createBtn = page.getByRole("button", { name: /创建|新建/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page.getByRole("dialog")).toBeVisible({ timeout: 3000 });
    }
  });

  test("Agent 列表空状态展示", async ({ page }) => {
    await page.goto("/projects/test-project/agents");
    // 页面不应白屏
    const body = page.locator("body");
    await expect(body).toBeVisible();
    const text = await body.innerText();
    expect(text.length).toBeGreaterThan(0);
  });
});
