import { expect, test } from "@playwright/test";

test("对话测试任务持续同步状态并链接真实 Run", async ({ page }) => {
  const now = "2026-07-12T00:00:00Z";
  let trustLoopRequests = 0;
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
    /\/api\/v1\/projects\/e2e-project\/runs\/run-1$/,
    async (route) => {
      await route.fulfill({
        json: {
          id: "run-1",
          project_id: "e2e-project",
          test_plan_version_id: "plan-version-1",
          status: "failed",
          total_cases: 1,
          passed_cases: 0,
          failed_cases: 1,
          error_cases: 0,
          cancelled_cases: 0,
          workflow_id: "run-run-1",
          created_at: now,
          started_at: now,
          completed_at: now,
        },
      });
    },
  );
  await page.route("**/runs/run-1/cases", async (route) => {
    await route.fulfill({ json: { items: [] } });
  });
  await page.route("**/runs/run-1/artifacts", async (route) => {
    await route.fulfill({ json: { items: [] } });
  });
  await page.route("**/runs/run-1/trust-loop", async (route) => {
    trustLoopRequests += 1;
    const pending = trustLoopRequests === 1;
    await route.fulfill({
      json: {
        job_id: pending ? null : "job-1",
        project_id: "e2e-project",
        run_id: "run-1",
        pipeline_version: "trust-loop-v1",
        status: pending ? "pending" : "completed_with_warnings",
        current_stage: pending ? null : "finalize",
        classifications: [],
        diagnostics: { status: "inconclusive", items: [] },
        regressions: [],
        calibration: { status: "inconclusive", metrics: {} },
        joint_gate: pending ? null : { decision: "block" },
        warning_codes: pending ? [] : ["diagnostic_model_unavailable"],
        error_type: null,
        created_at: pending ? null : now,
        updated_at: pending ? null : now,
        completed_at: pending ? null : now,
      },
    });
  });
  await page.route("**/runs/run-1/diagnostics**", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            id: "diagnostic-1",
            run_case_id: "case-1",
            pipeline_version: "trust-loop-v1",
            status: "inconclusive",
            failure_class: "target_failure",
            confidence: 0,
            evidence_ids: ["evidence-1"],
            summary: null,
            counterevidence: [],
            verification_steps: ["重放目标请求"],
            created_at: now,
            updated_at: now,
          },
        ],
        total: 1,
        limit: 100,
        offset: 0,
      },
    });
  });
  await page.route("**/runs/run-1/regressions**", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            id: "regression-1",
            run_case_id: "case-1",
            pipeline_version: "trust-loop-v1",
            fingerprint:
              "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            status: "quarantined",
            input_reference: {},
            minimized_input: null,
            reproduction_run_case_ids: ["evidence-1", "evidence-2"],
            reproduction_count: 2,
            target_dataset_version_id: null,
            created_at: now,
            updated_at: now,
          },
        ],
        total: 1,
        limit: 100,
        offset: 0,
      },
    });
  });
  await page.route("**/runs/run-1/calibration", async (route) => {
    await route.fulfill({
      json: {
        id: null,
        pipeline_version: "trust-loop-v1",
        status: "inconclusive",
        sample_set_version: null,
        metrics: {},
        arbitration: {},
        evaluator_version: null,
        created_at: null,
        updated_at: null,
      },
    });
  });
  await page.route("**/runs/run-1/joint-gate", async (route) => {
    await route.fulfill({
      json: {
        id: "gate-1",
        pipeline_version: "trust-loop-v1",
        status: "completed",
        baseline_run_id: null,
        decision: "block",
        rules: [
          {
            code: "evidence_completeness",
            status: "block",
            threshold: ">=0.8",
            actual: "0.5",
            reason: "证据完整性不足",
            evidence_refs: ["evidence-1"],
          },
        ],
        input_facts: {},
        explanation: "Deterministic joint gate decision",
        created_at: now,
      },
    });
  });
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

  await page.getByRole("link", { name: "查看运行详情" }).click();
  await expect(page.getByText("后处理排队中")).toBeVisible();
  await expect(page.getByText("完成（有警告）")).toBeVisible({
    timeout: 7000,
  });
  await expect(page.getByText("诊断无结论")).toBeVisible();
  await expect(page.getByText("隔离")).toBeVisible();
  await expect(page.getByText("门禁阻断")).toBeVisible();
  await expect(page.getByText("证据完整性不足")).toBeVisible();

  await page.setViewportSize({ width: 375, height: 812 });
  await expect(page.getByRole("region", { name: "可信闭环" })).toBeVisible();
  const overflow = await page.evaluate(() =>
    Array.from(document.querySelectorAll<HTMLElement>("body *"))
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          className: element.className.toString().slice(0, 160),
          left: Math.round(rect.left),
          right: Math.round(rect.right),
          tag: element.tagName,
        };
      })
      .filter((item) => item.left < -1 || item.right > window.innerWidth + 1)
      .slice(0, 10),
  );
  expect(overflow).toEqual([]);
});
