import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { CostEstimateCard } from "../cost-estimate-card";

const mockEstimate = {
  caseCount: 100,
  costPerCase: 0.5,
  estimatedTokens: 50000,
  estimatedDuration: 300,
};

describe("CostEstimateCard", () => {
  it("renders total cost", () => {
    render(<CostEstimateCard estimate={mockEstimate} />);

    expect(screen.getByText("总成本")).toBeInTheDocument();
    expect(screen.getByText(/\$50\.00/)).toBeInTheDocument();
  });

  it("renders token consumption", () => {
    render(<CostEstimateCard estimate={mockEstimate} />);

    expect(screen.getByText("Token 消耗")).toBeInTheDocument();
    expect(screen.getByText("50.0K")).toBeInTheDocument();
  });

  it("renders estimated duration", () => {
    render(<CostEstimateCard estimate={mockEstimate} />);

    expect(screen.getByText("预计时间")).toBeInTheDocument();
    expect(screen.getByText("5 分钟")).toBeInTheDocument();
  });

  it("renders case count", () => {
    render(<CostEstimateCard estimate={mockEstimate} />);

    expect(screen.getByText("用例数")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("shows warning when over threshold", () => {
    render(<CostEstimateCard costThreshold={30} estimate={mockEstimate} />);

    expect(screen.getByText("超出预算")).toBeInTheDocument();
    expect(screen.getByText(/是否继续执行/)).toBeInTheDocument();
  });

  it("does not show warning when under threshold", () => {
    render(<CostEstimateCard costThreshold={100} estimate={mockEstimate} />);

    expect(screen.queryByText("超出预算")).not.toBeInTheDocument();
  });

  it("renders confirm button", () => {
    const onConfirm = vi.fn();
    render(<CostEstimateCard estimate={mockEstimate} onConfirm={onConfirm} />);

    expect(screen.getByText("确认执行")).toBeInTheDocument();
  });

  it("renders cancel button", () => {
    const onCancel = vi.fn();
    render(<CostEstimateCard estimate={mockEstimate} onCancel={onCancel} />);

    expect(screen.getByText("取消")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button clicked", () => {
    const onConfirm = vi.fn();
    render(<CostEstimateCard estimate={mockEstimate} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByText("确认执行"));
    expect(onConfirm).toHaveBeenCalled();
  });

  it("calls onCancel when cancel button clicked", () => {
    const onCancel = vi.fn();
    render(<CostEstimateCard estimate={mockEstimate} onCancel={onCancel} />);

    fireEvent.click(screen.getByText("取消"));
    expect(onCancel).toHaveBeenCalled();
  });
});
