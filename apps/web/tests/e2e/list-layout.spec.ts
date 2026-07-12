import { expect, test, type Page } from "@playwright/test";

const longName =
  "Mission Acceptance 超长项目名称用于验证列表一屏显示、文本完整提示能力以及极端用户输入不会撑破操作列的稳定布局";

async function mockProjectList(page: Page) {
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        email: "admin@agenttest.local",
        id: "admin-1",
        display_name: "Admin",
        role: "super_admin",
        status: "active",
        must_change_password: false,
      },
    });
  });
  await page.route("**/api/v1/projects", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        contentType: "application/json",
        json: {
          items: Array.from({ length: 8 }, (_, index) => ({
            archived: index === 7,
            id: `project-${index}-with-a-long-stable-identifier`,
            name: `${longName} ${index + 1}`,
          })),
          next_cursor: null,
        },
      });
      return;
    }
    await route.continue();
  });
  await page.route("**/api/v1/projects/*", async (route) => {
    if (route.request().method() === "PATCH") {
      const body = route.request().postDataJSON() as { name: string };
      await route.fulfill({
        contentType: "application/json",
        json: {
          archived: false,
          id: "project-0-with-a-long-stable-identifier",
          name: body.name,
        },
      });
      return;
    }
    await route.continue();
  });
}

async function assertNoHorizontalOverflow(page: Page) {
  const measurements = await page.evaluate(() => ({
    bodyClientWidth: document.body.clientWidth,
    bodyScrollWidth: document.body.scrollWidth,
    documentClientWidth: document.documentElement.clientWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
  }));

  expect(measurements.bodyScrollWidth).toBeLessThanOrEqual(
    measurements.bodyClientWidth,
  );
  expect(measurements.documentScrollWidth).toBeLessThanOrEqual(
    measurements.documentClientWidth,
  );
}

for (const width of [1280, 1440, 1920]) {
  test(`project list fits every column at ${width}px`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ height: 900, width });
    await mockProjectList(page);
    await page.goto("/projects");

    await expect(page.getByRole("heading", { name: "项目管理" })).toBeVisible();
    await expect(
      page.getByRole("columnheader", { name: "操作" }),
    ).toBeVisible();
    await assertNoHorizontalOverflow(page);

    const firstRow = page.getByRole("row").filter({ hasText: `${longName} 1` });
    const actionGroup = firstRow.getByRole("group");
    const actionBox = await actionGroup.boundingBox();
    expect(actionBox).not.toBeNull();
    expect(actionBox!.x + actionBox!.width).toBeLessThanOrEqual(width);

    const projectName = firstRow.getByLabel(`${longName} 1`, { exact: true });
    const textMetrics = await projectName.evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
    }));
    expect(textMetrics.scrollWidth).toBeGreaterThan(textMetrics.clientWidth);

    await firstRow.getByRole("button", { name: `编辑${longName} 1` }).hover();
    const tooltip = firstRow.locator('[role="tooltip"][data-tooltip^="编辑"]');
    await expect(tooltip).toHaveCSS("opacity", "1");
    const iconMetrics = await firstRow
      .getByRole("button", { name: `编辑${longName} 1` })
      .locator("svg")
      .evaluate((icon) => {
        const box = icon.getBoundingClientRect();
        const style = getComputedStyle(icon);
        return {
          color: style.color,
          display: style.display,
          height: box.height,
          opacity: style.opacity,
          visibility: style.visibility,
          width: box.width,
        };
      });
    expect(iconMetrics).toMatchObject({
      display: "block",
      height: 16,
      opacity: "1",
      visibility: "visible",
      width: 16,
    });
    if (width === 1440) {
      await page.screenshot({
        fullPage: true,
        path: testInfo.outputPath("project-list-1440.png"),
      });
    }
  });
}

test("project edit uses a dialog and narrow screens never scroll sideways", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ height: 844, width: 390 });
  await mockProjectList(page);
  await page.goto("/projects");

  await assertNoHorizontalOverflow(page);
  const edit = page.getByRole("button", { name: `编辑${longName} 1` });
  await expect(edit).toBeVisible();
  await edit.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "编辑项目" })).toBeVisible();
  const nameInput = dialog.getByRole("textbox", { name: "项目名称" });
  await expect(nameInput).toHaveValue(`${longName} 1`);
  await nameInput.fill("移动端编辑后的项目名称");
  await page.getByRole("button", { name: "保存修改" }).click();
  await expect(page.getByRole("heading", { name: "编辑项目" })).toBeHidden();
  await assertNoHorizontalOverflow(page);
  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("project-list-390.png"),
  });
});
