import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RunResultWorkbench } from "../run-result-workbench";

describe("RunResultWorkbench", () => {
  const mockCases = [
    {
      id: "case-1",
      name: "Test Case 1",
      status: "passed" as const,
      duration_ms: 100,
      score: 0.95,
      error_type: null,
      error_message: null,
      input: { prompt: "create a banner" },
      output: { result: "ok" },
      trace: [
        {
          cost: 0.12,
          duration_ms: 60,
          event_type: "model_request",
          id: "span-1",
          name: "plan task",
          status: "ok",
          token_count: 120,
        },
        {
          duration_ms: 40,
          event_type: "tool_call",
          id: "span-2",
          name: "create asset",
          parent_event_id: "span-1",
          status: "ok",
        },
      ],
    },
    {
      id: "case-2",
      name: "Test Case 2",
      status: "failed" as const,
      duration_ms: 200,
      score: 0.6,
      error_type: "assertion_error",
      error_message: "Expected output to match",
      input: { prompt: "generate product copy" },
      output: { result: "off-topic" },
      trace: [
        {
          duration_ms: 200,
          event_type: "result",
          id: "span-3",
          name: "assert output",
          status: "failed",
        },
      ],
    },
    {
      id: "case-3",
      name: "Test Case 3",
      status: "error" as const,
      duration_ms: 50,
      score: null,
      error_type: "timeout",
      error_message: "Agent execution timed out",
      input: { prompt: "long running request" },
      output: null,
      trace: [
        {
          duration_ms: 50,
          event_type: "error",
          id: "span-4",
          name: "wait agent result",
          status: "error",
        },
      ],
    },
  ];

  const mockOnCaseSelect = vi.fn();

  beforeEach(() => {
    mockOnCaseSelect.mockClear();
    window.history.replaceState(null, "", "/projects/project-1/runs/run-1");
  });

  function renderWorkbench(cases = mockCases) {
    return render(
      <RunResultWorkbench
        cases={cases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );
  }

  it("renders three column layout", () => {
    renderWorkbench();

    // 左栏：用例列表
    expect(screen.getByText("用例列表")).toBeInTheDocument();

    // 中栏：用例详情
    expect(screen.getByText("用例详情")).toBeInTheDocument();

    // 右栏：评分面板
    expect(screen.getByText("评分结果")).toBeInTheDocument();
  });

  it("displays case list in left panel", () => {
    renderWorkbench();

    // 应该显示所有用例
    expect(
      screen.getByRole("button", { name: /Test Case 1/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Test Case 2/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Test Case 3/ }),
    ).toBeInTheDocument();
  });

  it("selects case when clicked", () => {
    renderWorkbench();

    // 点击用例
    fireEvent.click(screen.getByRole("button", { name: /Test Case 2/ }));

    // 应该调用 onCaseSelect
    expect(mockOnCaseSelect).toHaveBeenCalledWith("case-2");
    expect(
      screen.getByRole("heading", { name: "Test Case 2" }),
    ).toBeInTheDocument();
  });

  it("auto-selects the first matching case and syncs it to the URL", async () => {
    renderWorkbench();

    expect(
      screen.getByRole("heading", { name: "Test Case 1" }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(new URLSearchParams(window.location.search).get("case")).toBe(
        "case-1",
      );
    });
  });

  it("displays score in right panel", () => {
    renderWorkbench();

    // 右栏应该显示评分
    expect(screen.getByText("0.95")).toBeInTheDocument();
  });

  it("displays error information for failed cases", () => {
    renderWorkbench();

    // 点击失败用例
    fireEvent.click(screen.getByRole("button", { name: /Test Case 2/ }));

    // 应该显示错误信息
    expect(screen.getByText("assertion_error")).toBeInTheDocument();
    expect(screen.getByText("Expected output to match")).toBeInTheDocument();
    expect(screen.getByText("断言未通过")).toBeInTheDocument();
    expect(
      screen.getByText(/被测 Agent 已完成但结果不符合预期/),
    ).toBeInTheDocument();
  });

  it("supports filtering cases by status", () => {
    renderWorkbench();

    fireEvent.click(screen.getByRole("button", { name: /失败 1/ }));

    // 应该只显示失败用例
    expect(
      screen.queryByRole("button", { name: /Test Case 1/ }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Test Case 2/ }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Test Case 3/ }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Test Case 2" }),
    ).toBeInTheDocument();
    expect(new URLSearchParams(window.location.search).get("status")).toBe(
      "failed",
    );
  });

  it("supports keyword search while keeping the selected result visible", () => {
    renderWorkbench();

    fireEvent.change(screen.getByLabelText("搜索用例"), {
      target: { value: "timeout" },
    });

    expect(
      screen.queryByRole("button", { name: /Test Case 1/ }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Test Case 3/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Test Case 3" }),
    ).toBeInTheDocument();
    expect(new URLSearchParams(window.location.search).get("q")).toBe(
      "timeout",
    );
  });

  it("restores filter, query, and selected case from URL query", () => {
    window.history.replaceState(
      null,
      "",
      "/projects/project-1/runs/run-1?status=error&q=timeout&case=case-3",
    );

    renderWorkbench();

    expect(screen.getByLabelText("搜索用例")).toHaveValue("timeout");
    expect(
      screen.getByRole("button", { name: /Test Case 3/ }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Test Case 1/ }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Test Case 3" }),
    ).toBeInTheDocument();
  });

  it("distinguishes execution errors from assertion failures", () => {
    renderWorkbench();

    fireEvent.click(screen.getByRole("button", { name: /Test Case 3/ }));

    expect(screen.getByText("执行错误")).toBeInTheDocument();
    expect(
      screen.getByText(/优先排查环境、凭证、超时、网络或 Worker 错误/),
    ).toBeInTheDocument();
  });

  it("shows evidence summary from trace, output, duration, and cost", () => {
    renderWorkbench();

    const evidencePanel = screen.getByLabelText("当前用例证据概览");

    expect(within(evidencePanel).getByText("2 个")).toBeInTheDocument();
    expect(within(evidencePanel).getByText("已记录")).toBeInTheDocument();
    expect(within(evidencePanel).getByText("100 ms")).toBeInTheDocument();
    expect(within(evidencePanel).getByText("120")).toBeInTheDocument();
    expect(within(evidencePanel).getByText("¥0.12")).toBeInTheDocument();
  });

  it("displays empty state when no cases", () => {
    renderWorkbench([]);

    expect(screen.getByText("暂无用例数据")).toBeInTheDocument();
  });
});
