import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TrustLoopResult } from "../trust-loop-result";

describe("TrustLoopResult", () => {
  it("shows independent outcomes and the evidence-backed blocking rule", () => {
    render(
      <TrustLoopResult
        projectId="project-1"
        result={{
          outcomes: {
            execution: {
              status: "passed",
              code: "passed",
              evidence_ids: ["evidence-1"],
            },
            assertion: { status: "passed", code: "passed", evidence_ids: [] },
            quality: { status: "passed", code: "passed", evidence_ids: [] },
            security: {
              status: "failed",
              code: "critical_finding",
              evidence_ids: ["evidence-1"],
            },
          },
          diagnostics: [],
          regressions: [],
          gate: {
            status: "block",
            rules: [
              {
                code: "critical_security",
                status: "block",
                threshold: "<=0",
                actual: "1",
                reason: "检测到高危安全问题",
                evidence_refs: ["evidence-1"],
              },
            ],
          },
        }}
      />,
    );

    expect(screen.getByText("执行通过")).toBeVisible();
    expect(screen.getByText("安全阻断")).toBeVisible();
    expect(screen.getByText(/检测到高危安全问题/)).toBeVisible();
    expect(
      screen.getAllByRole("link", { name: "查看证据" })[0],
    ).toHaveAttribute("href", "/projects/project-1/runs/evidence/evidence-1");
  });

  it("renders review and quarantine without calling them failures", () => {
    render(
      <TrustLoopResult
        projectId="project-1"
        result={{
          outcomes: {
            execution: { status: "passed", code: "passed", evidence_ids: [] },
            assertion: { status: "passed", code: "passed", evidence_ids: [] },
            quality: {
              status: "needs_review",
              code: "uncalibrated",
              evidence_ids: ["e-2"],
            },
            security: { status: "passed", code: "passed", evidence_ids: [] },
          },
          diagnostics: [],
          regressions: [
            { id: "r-1", state: "quarantined", fingerprint: "abc" },
          ],
          gate: { status: "needs_review", rules: [] },
        }}
      />,
    );

    expect(screen.getByText("质量待复核")).toBeVisible();
    expect(screen.getByText(/隔离区/)).toBeVisible();
    expect(screen.getByText("门禁待复核")).toBeVisible();
  });
});
