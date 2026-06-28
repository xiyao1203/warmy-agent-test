import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { ScorerWeightConfig } from "../scorer-weight-config";
import type { ScorerWeight } from "../scorer-weight-config";

const mockScorers: ScorerWeight[] = [
  { id: "scorer-1", name: "准确性", weight: 40 },
  { id: "scorer-2", name: "质量", weight: 30 },
  { id: "scorer-3", name: "安全性", weight: 30 },
];

describe("ScorerWeightConfig", () => {
  it("renders all scorers", () => {
    render(
      <ScorerWeightConfig
        onChange={() => undefined}
        scorers={mockScorers}
      />,
    );

    expect(screen.getByText("准确性")).toBeInTheDocument();
    expect(screen.getByText("质量")).toBeInTheDocument();
    expect(screen.getByText("安全性")).toBeInTheDocument();
  });

  it("displays total weight", () => {
    render(
      <ScorerWeightConfig
        onChange={() => undefined}
        scorers={mockScorers}
      />,
    );

    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("shows warning when total is not 100%", () => {
    const incompleteScorers: ScorerWeight[] = [
      { id: "scorer-1", name: "准确性", weight: 50 },
      { id: "scorer-2", name: "质量", weight: 30 },
    ];

    render(
      <ScorerWeightConfig
        onChange={() => undefined}
        scorers={incompleteScorers}
      />,
    );

    expect(screen.getByText("80%")).toBeInTheDocument();
    expect(screen.getByText("权重总和应为 100%")).toBeInTheDocument();
  });

  it("calls onChange when weight changes", () => {
    const onChange = vi.fn();
    render(
      <ScorerWeightConfig
        onChange={onChange}
        scorers={mockScorers}
      />,
    );

    const inputs = screen.getAllByRole("spinbutton");
    fireEvent.change(inputs[0], { target: { value: "50" } });

    expect(onChange).toHaveBeenCalled();
  });

  it("disables inputs when disabled prop is true", () => {
    render(
      <ScorerWeightConfig
        disabled
        onChange={() => undefined}
        scorers={mockScorers}
      />,
    );

    const inputs = screen.getAllByRole("spinbutton");
    inputs.forEach((input) => {
      expect(input).toBeDisabled();
    });
  });

  it("renders empty state when no scorers", () => {
    render(
      <ScorerWeightConfig
        onChange={() => undefined}
        scorers={[]}
      />,
    );

    expect(screen.getByText("暂无评分器")).toBeInTheDocument();
  });

  it("displays weight percentages", () => {
    render(
      <ScorerWeightConfig
        onChange={() => undefined}
        scorers={mockScorers}
      />,
    );

    const inputs = screen.getAllByRole("spinbutton");
    expect(inputs).toHaveLength(3);
    expect(inputs[0]).toHaveValue(40);
    expect(inputs[1]).toHaveValue(30);
    expect(inputs[2]).toHaveValue(30);
  });
});
