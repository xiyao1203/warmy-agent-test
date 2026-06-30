import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

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
    },
    {
      id: "case-2",
      name: "Test Case 2",
      status: "failed" as const,
      duration_ms: 200,
      score: 0.6,
      error_type: "assertion_error",
      error_message: "Expected output to match",
    },
    {
      id: "case-3",
      name: "Test Case 3",
      status: "error" as const,
      duration_ms: 50,
      score: null,
      error_type: "timeout",
      error_message: "Agent execution timed out",
    },
  ];

  const mockOnCaseSelect = vi.fn();

  it("renders three column layout", () => {
    render(
      <RunResultWorkbench
        cases={mockCases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    // 左栏：用例列表
    expect(screen.getByText("用例列表")).toBeInTheDocument();

    // 中栏：用例详情
    expect(screen.getByText("用例详情")).toBeInTheDocument();

    // 右栏：评分面板
    expect(screen.getByText("评分结果")).toBeInTheDocument();
  });

  it("displays case list in left panel", () => {
    render(
      <RunResultWorkbench
        cases={mockCases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    // 应该显示所有用例
    expect(screen.getByText("Test Case 1")).toBeInTheDocument();
    expect(screen.getByText("Test Case 2")).toBeInTheDocument();
    expect(screen.getByText("Test Case 3")).toBeInTheDocument();
  });

  it("selects case when clicked", () => {
    render(
      <RunResultWorkbench
        cases={mockCases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    // 点击用例
    fireEvent.click(screen.getByText("Test Case 1"));

    // 应该调用 onCaseSelect
    expect(mockOnCaseSelect).toHaveBeenCalledWith("case-1");
  });

  it("displays case details in middle panel", () => {
    render(
      <RunResultWorkbench
        cases={mockCases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    // 点击用例
    fireEvent.click(screen.getByText("Test Case 1"));

    // 中栏应该显示用例详情 - 使用 getAllByText 因为可能有多个
    const caseNames = screen.getAllByText("Test Case 1");
    expect(caseNames.length).toBeGreaterThanOrEqual(1);
    // 检查 duration 显示 - 使用 getAllByText 因为可能有多个
    const durations = screen.getAllByText("100ms");
    expect(durations.length).toBeGreaterThanOrEqual(1);
  });

  it("displays score in right panel", () => {
    render(
      <RunResultWorkbench
        cases={mockCases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    // 点击用例
    fireEvent.click(screen.getByText("Test Case 1"));

    // 右栏应该显示评分
    expect(screen.getByText("0.95")).toBeInTheDocument();
  });

  it("displays error information for failed cases", () => {
    render(
      <RunResultWorkbench
        cases={mockCases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    // 点击失败用例
    fireEvent.click(screen.getByText("Test Case 2"));

    // 应该显示错误信息
    expect(screen.getByText("assertion_error")).toBeInTheDocument();
    expect(screen.getByText("Expected output to match")).toBeInTheDocument();
  });

  it("supports filtering cases by status", () => {
    render(
      <RunResultWorkbench
        cases={mockCases}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    // 点击筛选按钮 - 使用 getAllByText 因为可能有多个
    const filterButtons = screen.getAllByText("失败");
    // 第一个是筛选按钮
    fireEvent.click(filterButtons[0]);

    // 应该只显示失败用例
    expect(screen.queryByText("Test Case 1")).not.toBeInTheDocument();
    expect(screen.getByText("Test Case 2")).toBeInTheDocument();
    expect(screen.queryByText("Test Case 3")).not.toBeInTheDocument();
  });

  it("displays empty state when no cases", () => {
    render(
      <RunResultWorkbench
        cases={[]}
        onCaseSelect={mockOnCaseSelect}
        projectId="project-1"
        runId="run-1"
      />,
    );

    expect(screen.getByText("暂无用例数据")).toBeInTheDocument();
  });
});
