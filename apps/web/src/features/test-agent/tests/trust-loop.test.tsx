import { render, screen } from "@testing-library/react";
import type { RunTrustLoopData } from "@/features/runs";
import { expect, it } from "vitest";

import { TrustLoopResult } from "../trust-loop-result";

it("reuses the persisted Run trust-loop view in Test Agent", () => {
  const data: RunTrustLoopData = {
    summary: {
      job_id: "job-1",
      project_id: "project-1",
      run_id: "run-1",
      pipeline_version: "trust-loop-v1",
      status: "completed_with_warnings",
      current_stage: "finalize",
      classifications: [],
      diagnostics: { status: "inconclusive", items: [] },
      regressions: [],
      calibration: { status: "inconclusive", metrics: {} },
      joint_gate: { decision: "quarantine" },
      warning_codes: ["diagnostic_model_unavailable"],
      error_type: null,
      created_at: "2026-07-12T00:00:00Z",
      updated_at: "2026-07-12T00:00:00Z",
      completed_at: "2026-07-12T00:00:00Z",
    },
    diagnostics: [],
    regressions: [],
    calibration: {
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
    gate: {
      id: null,
      pipeline_version: "trust-loop-v1",
      status: "completed",
      baseline_run_id: null,
      decision: "quarantine",
      rules: [],
      input_facts: {},
      explanation: null,
      created_at: null,
    },
  };

  render(<TrustLoopResult data={data} projectId="project-1" runId="run-1" />);

  expect(screen.getByText("完成（有警告）")).toBeVisible();
  expect(screen.getByText("门禁隔离")).toBeVisible();
  expect(screen.getByText("暂无回归候选")).toBeVisible();
});
