import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { FailureToRegression } from "../failure-to-regression";

const mockFailures = [
  {
    id: "fail-1",
    reason: "输出不匹配",
    input: "用户查询内容",
    expectedOutput: "预期输出内容",
    actualOutput: "实际输出内容",
  },
  {
    id: "fail-2",
    reason: "超时",
    input: "另一个查询",
    expectedOutput: "另一个预期",
    actualOutput: "另一个实际",
  },
];

describe("FailureToRegression", () => {
  it("renders failure count", () => {
    render(<FailureToRegression failures={mockFailures} />);

    expect(screen.getByText("失败用例转换")).toBeInTheDocument();
    expect(screen.getByText("2 项")).toBeInTheDocument();
  });

  it("renders failure items", () => {
    render(<FailureToRegression failures={mockFailures} />);

    expect(screen.getByText("fail-1")).toBeInTheDocument();
    expect(screen.getByText("fail-2")).toBeInTheDocument();
  });

  it("renders failure reason", () => {
    render(<FailureToRegression failures={mockFailures} />);

    expect(screen.getByText("输出不匹配")).toBeInTheDocument();
    expect(screen.getByText("超时")).toBeInTheDocument();
  });

  it("selects failure item", () => {
    render(<FailureToRegression failures={mockFailures} />);

    const checkbox = screen.getAllByRole("checkbox")[0];
    fireEvent.click(checkbox);
    expect(screen.getByText("已选 1 项")).toBeInTheDocument();
  });

  it("selects all failures", () => {
    render(<FailureToRegression failures={mockFailures} />);

    fireEvent.click(screen.getByText("全选"));
    expect(screen.getByText("已选 2 项")).toBeInTheDocument();
  });

  it("deselects all failures", () => {
    render(<FailureToRegression failures={mockFailures} />);

    fireEvent.click(screen.getByText("全选"));
    fireEvent.click(screen.getByText("取消全选"));
    expect(screen.getByText("已选 0 项")).toBeInTheDocument();
  });

  it("disables convert button when no selection", () => {
    render(<FailureToRegression failures={mockFailures} />);

    const button = screen.getByRole("button", { name: /转换为回归用例/ });
    expect(button).toBeDisabled();
  });

  it("enables convert button when selected", () => {
    render(<FailureToRegression failures={mockFailures} />);

    const checkbox = screen.getAllByRole("checkbox")[0];
    fireEvent.click(checkbox);

    const button = screen.getByRole("button", { name: /转换为回归用例/ });
    expect(button).not.toBeDisabled();
  });

  it("calls onConvert with selected ids", () => {
    const onConvert = vi.fn();
    render(
      <FailureToRegression
        failures={mockFailures}
        onConvert={onConvert}
      />,
    );

    const checkbox = screen.getAllByRole("checkbox")[0];
    fireEvent.click(checkbox);

    const button = screen.getByRole("button", { name: /转换为回归用例/ });
    fireEvent.click(button);

    expect(onConvert).toHaveBeenCalledWith(["fail-1"]);
  });
});
