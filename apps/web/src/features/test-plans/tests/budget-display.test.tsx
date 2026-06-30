import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { BudgetDisplay } from "../budget-display";

describe("BudgetDisplay", () => {
  it("renders labels", () => {
    render(<BudgetDisplay budget={100} used={0} />);

    expect(screen.getByText("预算")).toBeInTheDocument();
    expect(screen.getByText("已用")).toBeInTheDocument();
    expect(screen.getByText("剩余")).toBeInTheDocument();
  });

  it("displays usage percentage", () => {
    render(<BudgetDisplay budget={100} used={50} />);

    expect(screen.getByText("50.0%")).toBeInTheDocument();
  });

  it("shows warning when usage is 80%", () => {
    render(<BudgetDisplay budget={100} used={85} />);

    expect(
      screen.getByText("预算使用已达 80%，请注意控制成本"),
    ).toBeInTheDocument();
  });

  it("shows exceeded warning when usage is 100%", () => {
    render(<BudgetDisplay budget={100} used={110} />);

    expect(screen.getByText("预算已超支，建议停止执行")).toBeInTheDocument();
  });

  it("applies warning styles", () => {
    render(<BudgetDisplay budget={100} used={85} />);

    const percentage = screen.getByText("85.0%");
    expect(percentage).toHaveClass("text-[var(--warning)]");
  });

  it("applies exceeded styles", () => {
    render(<BudgetDisplay budget={100} used={110} />);

    const percentage = screen.getByText("110.0%");
    expect(percentage).toHaveClass("text-[var(--danger)]");
  });

  it("calculates usage percent from props", () => {
    render(<BudgetDisplay budget={100} usagePercent={75} used={50} />);

    expect(screen.getByText("75.0%")).toBeInTheDocument();
  });

  it("no warning when usage is below 80%", () => {
    render(<BudgetDisplay budget={100} used={50} />);

    expect(
      screen.queryByText("预算使用已达 80%，请注意控制成本"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("预算已超支，建议停止执行"),
    ).not.toBeInTheDocument();
  });
});
