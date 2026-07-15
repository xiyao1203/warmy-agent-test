import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";

type NavigationBaseline = {
  maximumRegressionRatio: number;
  routes: Record<string, number>;
  samplesPerRoute: number;
};

const baseline = JSON.parse(
  readFileSync(
    resolve(process.cwd(), "../../docs/performance/navigation-baseline.json"),
    "utf8",
  ),
) as NavigationBaseline;

async function navigationMedian(page: Page, route: string) {
  const samples: number[] = [];
  for (let index = 0; index < baseline.samplesPerRoute; index += 1) {
    await page.goto(route, { waitUntil: "load" });
    samples.push(
      await page.evaluate(() => {
        const navigation = performance.getEntriesByType("navigation")[0] as
          | PerformanceNavigationTiming
          | undefined;
        return navigation?.domInteractive ?? Number.POSITIVE_INFINITY;
      }),
    );
  }
  return samples.sort((left, right) => left - right)[
    Math.floor(samples.length / 2)
  ];
}

test("authenticated navigation stays within the recorded local baseline", async ({
  page,
}) => {
  const email = process.env.E2E_ADMIN_EMAIL;
  const password = process.env.E2E_ADMIN_PASSWORD;
  const projectId = process.env.E2E_PROJECT_ID;
  test.skip(
    !email || !password || !projectId,
    "Authenticated services are unavailable: set E2E_ADMIN_EMAIL, E2E_ADMIN_PASSWORD, and E2E_PROJECT_ID.",
  );

  const loginMedian = await navigationMedian(page, "/login");
  if (!(await page.getByLabel("邮箱").isVisible())) {
    await page.getByRole("button", { name: "登录" }).first().click();
  }
  await page.getByLabel("邮箱").fill(email!);
  await page.getByLabel("密码").fill(password!);
  await page.getByRole("button", { name: "登录" }).click();
  try {
    await expect(page).toHaveURL(/\/projects\//, { timeout: 5000 });
  } catch {
    test.skip(
      true,
      "Authenticated Control API is unavailable for navigation sampling.",
    );
  }

  const routes = {
    "/login": loginMedian,
    "/projects": await navigationMedian(page, "/projects"),
    "/projects/[projectId]/runs": await navigationMedian(
      page,
      `/projects/${projectId}/runs`,
    ),
    "/projects/[projectId]/test-agent": await navigationMedian(
      page,
      `/projects/${projectId}/test-agent`,
    ),
  };

  for (const [route, actual] of Object.entries(routes)) {
    const expected = baseline.routes[route];
    expect(
      actual,
      `${route} median domInteractive ${actual}ms exceeds the ${expected}ms baseline`,
    ).toBeLessThanOrEqual(expected * (1 + baseline.maximumRegressionRatio));
  }
});
