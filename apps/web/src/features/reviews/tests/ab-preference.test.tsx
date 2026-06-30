import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { ABPreferenceSelector, ABReviewPanel } from "../ab-preference";

describe("ABPreferenceSelector", () => {
  it("renders all three options", () => {
    render(<ABPreferenceSelector onChange={() => undefined} value={null} />);

    expect(screen.getByText("A 更好")).toBeInTheDocument();
    expect(screen.getByText("相同")).toBeInTheDocument();
    expect(screen.getByText("B 更好")).toBeInTheDocument();
  });

  it("calls onChange when option is clicked", () => {
    const onChange = vi.fn();
    render(<ABPreferenceSelector onChange={onChange} value={null} />);

    fireEvent.click(screen.getByText("A 更好"));
    expect(onChange).toHaveBeenCalledWith("a");
  });

  it("does not call onChange when disabled", () => {
    const onChange = vi.fn();
    render(<ABPreferenceSelector disabled onChange={onChange} value={null} />);

    fireEvent.click(screen.getByText("A 更好"));
    expect(onChange).not.toHaveBeenCalled();
  });

  it("applies selected styles to active option", () => {
    render(<ABPreferenceSelector onChange={() => undefined} value="a" />);

    const buttons = screen.getAllByRole("radio");
    expect(buttons[0]).toHaveAttribute("aria-checked", "true");
    expect(buttons[1]).toHaveAttribute("aria-checked", "false");
    expect(buttons[2]).toHaveAttribute("aria-checked", "false");
  });
});

describe("ABReviewPanel", () => {
  it("renders output A and B", () => {
    render(
      <ABReviewPanel
        onOpinionChange={() => undefined}
        onPreferenceChange={() => undefined}
        opinion=""
        outputA="输出 A 内容"
        outputB="输出 B 内容"
        preference={null}
      />,
    );

    expect(screen.getByText("版本 A")).toBeInTheDocument();
    expect(screen.getByText("版本 B")).toBeInTheDocument();
    expect(screen.getByText("输出 A 内容")).toBeInTheDocument();
    expect(screen.getByText("输出 B 内容")).toBeInTheDocument();
  });

  it("renders preference selector", () => {
    render(
      <ABReviewPanel
        onOpinionChange={() => undefined}
        onPreferenceChange={() => undefined}
        opinion=""
        outputA="A"
        outputB="B"
        preference={null}
      />,
    );

    expect(screen.getByText("A 更好")).toBeInTheDocument();
    expect(screen.getByText("相同")).toBeInTheDocument();
    expect(screen.getByText("B 更好")).toBeInTheDocument();
  });

  it("renders opinion textarea with initial value", () => {
    render(
      <ABReviewPanel
        onOpinionChange={() => undefined}
        onPreferenceChange={() => undefined}
        opinion="初始意见"
        outputA="A"
        outputB="B"
        preference={null}
      />,
    );

    const textarea = screen.getByPlaceholderText("可选：添加审核意见");
    expect(textarea).toHaveValue("初始意见");
  });

  it("calls onOpinionChange when textarea changes", () => {
    const onOpinionChange = vi.fn();
    render(
      <ABReviewPanel
        onOpinionChange={onOpinionChange}
        onPreferenceChange={() => undefined}
        opinion=""
        outputA="A"
        outputB="B"
        preference={null}
      />,
    );

    const textarea = screen.getByPlaceholderText("可选：添加审核意见");
    fireEvent.change(textarea, { target: { value: "新意见" } });
    expect(onOpinionChange).toHaveBeenCalledWith("新意见");
  });

  it("calls onPreferenceChange when preference selected", () => {
    const onPreferenceChange = vi.fn();
    render(
      <ABReviewPanel
        onOpinionChange={() => undefined}
        onPreferenceChange={onPreferenceChange}
        opinion=""
        outputA="A"
        outputB="B"
        preference={null}
      />,
    );

    fireEvent.click(screen.getByText("B 更好"));
    expect(onPreferenceChange).toHaveBeenCalledWith("b");
  });
});
