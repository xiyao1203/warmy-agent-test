import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { RunTrustLoopData } from "../api";
import { TrustLoopPanel } from "../trust-loop-panel";

const now = "2026-07-12T00:00:00Z";

function data(status = "completed_with_warnings"): RunTrustLoopData {
  return {
    calibration: {
      arbitration: {},
      created_at: now,
      evaluator_version: null,
      id: "calibration-1",
      metrics: { accuracy: 0.75, calibrated: false },
      pipeline_version: "trust-loop-v1",
      sample_set_version: null,
      status: "completed",
      updated_at: now,
    },
    diagnostics: [
      {
        confidence: 0,
        counterevidence: [],
        created_at: now,
        evidence_ids: ["evidence-1"],
        failure_class: "target_failure",
        id: "diagnostic-1",
        pipeline_version: "trust-loop-v1",
        run_case_id: "case-1",
        status: "inconclusive",
        summary: null,
        updated_at: now,
        verification_steps: ["重放目标请求"],
      },
    ],
    gate: {
      baseline_run_id: null,
      created_at: now,
      decision: "block",
      explanation: "Deterministic joint gate decision",
      id: "gate-1",
      input_facts: {},
      pipeline_version: "trust-loop-v1",
      rules: [
        {
          actual: "0.5",
          code: "evidence_completeness",
          evidence_refs: ["evidence-1"],
          reason: "证据完整性不足",
          status: "block",
          threshold: ">=0.8",
        },
      ],
      status: "completed",
    },
    regressions: [
      {
        created_at: now,
        fingerprint: "a".repeat(64),
        id: "regression-1",
        input_reference: { run_case_id: "case-1" },
        minimized_input: null,
        pipeline_version: "trust-loop-v1",
        reproduction_count: 2,
        reproduction_run_case_ids: ["evidence-1", "evidence-2"],
        run_case_id: "case-1",
        status: "quarantined",
        target_dataset_version_id: null,
        updated_at: now,
      },
    ],
    summary: {
      calibration: { status: "completed" },
      classifications: [
        {
          code: "target_5xx",
          confidence: 1,
          evidence_ids: ["evidence-1"],
          failure_class: "target_failure",
          run_case_id: "case-1",
        },
      ],
      completed_at: now,
      created_at: now,
      current_stage: "finalize",
      diagnostics: { items: [], status: "inconclusive" },
      error_type: null,
      job_id: "job-1",
      joint_gate: { decision: "block" },
      pipeline_version: "trust-loop-v1",
      project_id: "project-1",
      regressions: [],
      run_id: "run-1",
      status,
      updated_at: now,
      warning_codes: ["diagnostic_model_unavailable"],
    },
  };
}

describe("TrustLoopPanel", () => {
  it("shows stable pending progress without inventing results", () => {
    const pending = data("pending");
    pending.summary.current_stage = null;
    pending.diagnostics = [];
    pending.regressions = [];
    pending.gate = {
      ...pending.gate,
      decision: null,
      id: null,
      status: "pending",
    };

    render(
      <TrustLoopPanel data={pending} projectId="project-1" runId="run-1" />,
    );

    expect(screen.getByText("可信闭环")).toBeVisible();
    expect(screen.getByText("后处理排队中")).toBeVisible();
    expect(screen.getByText("暂无诊断结论")).toBeVisible();
    expect(screen.getByText("暂无回归候选")).toBeVisible();
  });

  it("renders warning, inconclusive, quarantine, blocking rules and evidence links", () => {
    render(
      <TrustLoopPanel
        compact
        data={data()}
        projectId="project-1"
        runId="run-1"
      />,
    );

    expect(screen.getByText("完成（有警告）")).toBeVisible();
    expect(screen.getByText("诊断无结论")).toBeVisible();
    expect(screen.getByText("隔离")).toBeVisible();
    expect(screen.getByText("门禁阻断")).toBeVisible();
    expect(screen.getByText("证据完整性不足")).toBeVisible();
    expect(screen.getByRole("link", { name: "查看用例证据" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs/run-1?case=case-1&evidence=evidence-1",
    );
  });
});
