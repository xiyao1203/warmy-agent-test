import { expect, test, type Page } from "@playwright/test";

async function mockSession(page: Page) {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({
      contentType: "application/json",
      json: {
        display_name: "Admin",
        email: "admin@agenttest.local",
        id: "admin-1",
        must_change_password: false,
        role: "super_admin",
        status: "active",
      },
    }),
  );
}

function project(index: number) {
  return {
    active_environment_count: 0,
    agent_count: 1,
    archived: false,
    created_at: "2026-07-20T00:00:00Z",
    created_by: "admin-1",
    dataset_count: 1,
    description: `分页验收项目 ${index}`,
    id: `project-${index}`,
    key: `PAGE-${String(index).padStart(2, "0")}`,
    last_run: null,
    last_run_at: null,
    lead_user_id: "admin-1",
    member_count: 2,
    name: `分页验收项目 ${index}`,
    open_review_count: 0,
    status: "active",
    test_case_count: 3,
    test_plan_count: 1,
    updated_at: "2026-07-20T00:00:00Z",
    updated_by: "admin-1",
  };
}

test("project list keeps standard pagination in the URL and compact viewport", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ height: 900, width: 1440 });
  await mockSession(page);
  const allProjects = Array.from({ length: 21 }, (_, index) =>
    project(index + 1),
  );
  await page.route("**/api/v1/projects**", async (route) => {
    if (route.request().method() !== "GET") return route.continue();
    const url = new URL(route.request().url());
    const currentPage = Number(url.searchParams.get("page") ?? 1);
    const pageSize = Number(url.searchParams.get("page_size") ?? 10);
    const start = (currentPage - 1) * pageSize;
    await route.fulfill({
      contentType: "application/json",
      json: {
        items: allProjects.slice(start, start + pageSize),
        page: currentPage,
        page_size: pageSize,
        total: allProjects.length,
        total_pages: Math.ceil(allProjects.length / pageSize),
      },
    });
  });

  await page.goto("/projects");
  await expect(page.getByRole("navigation", { name: "分页" })).toBeVisible();
  await expect(page.getByText("共 21 条")).toBeVisible();
  await expect(page.getByText("第 1 / 3 页")).toBeVisible();

  const controls = page.locator("[data-pagination-controls]");
  const paginationFooter = controls.locator("..");
  const desktopGeometry = await controls.evaluate((element) => {
    const footer = element.parentElement!;
    const total = footer.querySelector("[data-pagination-total]")!;
    const controlsRect = element.getBoundingClientRect();
    const footerRect = footer.getBoundingClientRect();
    const totalRect = total.getBoundingClientRect();
    return {
      controlsLeft: controlsRect.left,
      justifyContent: getComputedStyle(element).justifyContent,
      rightInset:
        footerRect.right -
        Number.parseFloat(getComputedStyle(footer).paddingRight) -
        controlsRect.right,
      totalRight: totalRect.right,
    };
  });
  expect(desktopGeometry.justifyContent).toBe("flex-end");
  expect(desktopGeometry.controlsLeft).toBeGreaterThanOrEqual(
    desktopGeometry.totalRight,
  );
  expect(Math.abs(desktopGeometry.rightInset)).toBeLessThanOrEqual(1);
  await paginationFooter.screenshot({
    path: testInfo.outputPath("pagination-footer-1440.png"),
  });

  await page.getByRole("button", { name: "下一页" }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(page.getByLabel("分页验收项目 11").first()).toBeVisible();

  await page.getByRole("combobox", { name: "每页条数" }).selectOption("20");
  await expect(page).toHaveURL(/page=1/);
  await expect(page).toHaveURL(/page_size=20/);
  await expect(page.getByText("第 1 / 2 页")).toBeVisible();

  await page.setViewportSize({ height: 844, width: 390 });
  const mobileGeometry = await controls.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return {
      clientWidth: element.clientWidth,
      justifyContent: getComputedStyle(element).justifyContent,
      right: rect.right,
      scrollWidth: element.scrollWidth,
    };
  });
  expect(mobileGeometry.justifyContent).toBe("flex-end");
  expect(mobileGeometry.scrollWidth).toBeLessThanOrEqual(
    mobileGeometry.clientWidth,
  );
  expect(mobileGeometry.right).toBeLessThanOrEqual(390);
  const overflow = await page.evaluate(
    () =>
      document.documentElement.scrollWidth -
      document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
  await paginationFooter.screenshot({
    path: testInfo.outputPath("pagination-footer-390.png"),
  });
});
