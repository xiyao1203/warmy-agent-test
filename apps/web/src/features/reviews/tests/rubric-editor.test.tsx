import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import {
  RubricEditor,
  RubricDisplay,
} from "../rubric-editor";
import type { RubricDimension } from "../rubric-editor";

const mockDimensions: RubricDimension[] = [
  {
    id: "quality",
    name: "质量",
    description: "输出质量",
    score: 4,
    comment: "不错",
  },
  {
    id: "accuracy",
    name: "准确性",
    description: "事实准确性",
    score: 3,
    comment: "",
  },
  {
    id: "safety",
    name: "安全性",
    description: "内容安全性",
    score: 5,
    comment: "安全",
  },
];

describe("RubricEditor", () => {
  it("renders all dimensions", () => {
    render(
      <RubricEditor
        dimensions={mockDimensions}
        onDimensionsChange={() => undefined}
      />,
    );

    expect(screen.getByText("质量")).toBeInTheDocument();
    expect(screen.getByText("准确性")).toBeInTheDocument();
    expect(screen.getByText("安全性")).toBeInTheDocument();
  });

  it("displays total score", () => {
    render(
      <RubricEditor
        dimensions={mockDimensions}
        onDimensionsChange={() => undefined}
      />,
    );

    expect(screen.getByText("12 / 15")).toBeInTheDocument();
  });

  it("calls onDimensionsChange when score changes", () => {
    const onDimensionsChange = vi.fn();
    render(
      <RubricEditor
        dimensions={mockDimensions}
        onDimensionsChange={onDimensionsChange}
      />,
    );

    const inputs = screen.getAllByRole("spinbutton");
    fireEvent.change(inputs[0], { target: { value: "5" } });

    expect(onDimensionsChange).toHaveBeenCalled();
  });

  it("calls onDimensionsChange when comment changes", () => {
    const onDimensionsChange = vi.fn();
    render(
      <RubricEditor
        dimensions={mockDimensions}
        onDimensionsChange={onDimensionsChange}
      />,
    );

    const inputs = screen.getAllByPlaceholderText("评分说明（可选）");
    fireEvent.change(inputs[0], { target: { value: "新说明" } });

    expect(onDimensionsChange).toHaveBeenCalled();
  });

  it("disables inputs when disabled prop is true", () => {
    render(
      <RubricEditor
        disabled
        dimensions={mockDimensions}
        onDimensionsChange={() => undefined}
      />,
    );

    const inputs = screen.getAllByRole("spinbutton");
    inputs.forEach((input) => {
      expect(input).toBeDisabled();
    });
  });

  it("renders empty state when no dimensions", () => {
    render(
      <RubricEditor
        dimensions={[]}
        onDimensionsChange={() => undefined}
      />,
    );

    expect(screen.getByText("暂无评分维度")).toBeInTheDocument();
  });
});

describe("RubricDisplay", () => {
  it("renders all dimensions", () => {
    render(<RubricDisplay dimensions={mockDimensions} />);

    expect(screen.getByText("质量")).toBeInTheDocument();
    expect(screen.getByText("准确性")).toBeInTheDocument();
    expect(screen.getByText("安全性")).toBeInTheDocument();
  });

  it("displays total score", () => {
    render(<RubricDisplay dimensions={mockDimensions} />);

    expect(screen.getByText("12 / 15")).toBeInTheDocument();
  });

  it("displays dimension scores", () => {
    render(<RubricDisplay dimensions={mockDimensions} />);

    expect(screen.getByText("4 / 5")).toBeInTheDocument();
    expect(screen.getByText("3 / 5")).toBeInTheDocument();
    expect(screen.getByText("5 / 5")).toBeInTheDocument();
  });

  it("displays comments", () => {
    render(<RubricDisplay dimensions={mockDimensions} />);

    expect(screen.getByText("不错")).toBeInTheDocument();
    expect(screen.getByText("安全")).toBeInTheDocument();
  });

  it("renders null when no dimensions", () => {
    const { container } = render(<RubricDisplay dimensions={[]} />);

    expect(container.firstChild).toBeNull();
  });
});
