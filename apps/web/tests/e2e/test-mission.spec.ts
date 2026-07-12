import { expect, test } from "@playwright/test";

test("对话测试任务持续同步状态并链接真实 Run", async ({ page }) => {
  const now = "2026-07-12T00:00:00Z";
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      json: {
        id: "user-1",
        email: "e2e@example.com",
        display_name: "E2E",
        role: "developer",
        status: "active",
        must_change_password: false,
      },
    });
  });
  await page.route("**/api/v1/projects", async (route) => {
    await route.fulfill({
      json: {
        items: [{ id: "e2e-project", name: "E2E 项目", description: null }],
      },
    });
  });
  await page.route(
    "**/api/v1/projects/e2e-project/test-agent/sessions**",
    async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith("/events")) {
        await route.fulfill({
          body: "event: stream.ready\ndata: {}\n\n",
          contentType: "text/event-stream",
          status: 200,
        });
        return;
      }
      if (url.pathname.endsWith("/sessions")) {
        await route.fulfill({
          json: {
            items: [
              {
                session_id: "session-1",
                title: "全链路测试",
                status: "active",
                updated_at: now,
              },
            ],
          },
        });
        return;
      }
      await route.fulfill({
        json: {
          session_id: "session-1",
          title: "全链路测试",
          status: "active",
          updated_at: now,
          messages: [
            {
              message_id: "message-1",
              sequence: 1,
              role: "user",
              content: "测试目标 Agent",
              timestamp: now,
            },
          ],
          artifacts: [
            { type: "test_mission", id: "mission-1", relation: "updated" },
          ],
          protocol_version: 1,
          plan_draft: {},
          event_cursor: 2,
          active_generation: null,
          timeline: [
            {
              kind: "event",
              id: "event-1",
              timestamp: now,
              event_type: "agent.completed",
              event_sequence: 2,
              generation_id: null,
              payload: {
                task_id: "task-1",
                capability: "test_missions.confirm_and_start",
                output: { mission_id: "mission-1", status: "running" },
              },
            },
          ],
        },
      });
    },
  );
  await page.route(
    "**/api/v1/projects/e2e-project/test-missions/mission-1",
    async (route) => {
      await route.fulfill({
        json: {
          mission_id: "mission-1",
          project_id: "e2e-project",
          session_id: "session-1",
          status: "completed",
          active_revision_id: "revision-1",
          workflow_id: "workflow-1",
          facts: {},
          ready: true,
          missing_inputs: [],
          execution_channels: ["browser", "security"],
          action_allowlist: ["read"],
          inferred_scenarios: [],
          revision_hash: null,
          snapshot: null,
          updated_at: now,
          assets: [
            {
              type: "run",
              id: "run-1",
              relation: "created",
              stage: "start_run",
            },
          ],
        },
      });
    },
  );

  await page.goto("/projects/e2e-project/test-agent?session=session-1");

  await expect(page.getByText("全链路测试已完成")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "查看运行详情" }),
  ).toHaveAttribute("href", "/projects/e2e-project/runs/run-1");
});
