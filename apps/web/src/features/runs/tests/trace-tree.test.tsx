import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { TraceTree, TraceSpan } from "../trace-tree";

describe("TraceTree", () => {
  const mockSpans: TraceSpan[] = [
    {
      id: "span-1",
      name: "Agent Start",
      event_type: "step",
      duration_ms: 100,
      token_count: 50,
      cost: 0.05,
      parent_event_id: null,
      status: "ok",
    },
    {
      id: "span-2",
      name: "Model Request",
      event_type: "model_request",
      duration_ms: 200,
      token_count: 100,
      cost: 0.1,
      parent_event_id: "span-1",
      status: "ok",
    },
    {
      id: "span-3",
      name: "Tool Call",
      event_type: "tool_call",
      duration_ms: 50,
      token_count: null,
      cost: null,
      parent_event_id: "span-1",
      status: "ok",
    },
    {
      id: "span-4",
      name: "Error Span",
      event_type: "error",
      duration_ms: 10,
      token_count: null,
      cost: null,
      parent_event_id: "span-2",
      status: "error",
    },
  ];

  it("renders empty state when no spans", () => {
    render(<TraceTree spans={[]} />);
    expect(screen.getByText("暂无 Trace 数据")).toBeInTheDocument();
  });

  it("renders trace tree with correct structure", () => {
    render(<TraceTree spans={mockSpans} />);

    // 应该显示根节点
    expect(screen.getByText("Agent Start")).toBeInTheDocument();

    // 展开的节点应该显示子节点
    expect(screen.getByText("Model Request")).toBeInTheDocument();
    expect(screen.getByText("Tool Call")).toBeInTheDocument();
  });

  it("displays span metadata correctly", () => {
    render(<TraceTree spans={mockSpans} />);

    // 检查 duration 显示
    expect(screen.getByText("100ms")).toBeInTheDocument();
    expect(screen.getByText("200ms")).toBeInTheDocument();

    // 检查 token count 显示
    expect(screen.getByText("50")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();

    // 检查 cost 显示
    expect(screen.getByText("¥0.05")).toBeInTheDocument();
    expect(screen.getByText("¥0.10")).toBeInTheDocument();
  });

  it("displays status badges correctly", () => {
    render(<TraceTree spans={mockSpans} />);

    // 检查状态标签 - 使用 getAllByText 因为可能有多个
    const okBadges = screen.getAllByText("ok");
    expect(okBadges.length).toBeGreaterThanOrEqual(3);

    // error 状态在 error 事件类型和 status 中都会出现
    const errorElements = screen.getAllByText("error");
    expect(errorElements.length).toBeGreaterThanOrEqual(1);
  });

  it("displays event type badges with correct colors", () => {
    render(<TraceTree spans={mockSpans} />);

    // 检查事件类型标签
    expect(screen.getByText("step")).toBeInTheDocument();
    expect(screen.getByText("model_request")).toBeInTheDocument();
    expect(screen.getByText("tool_call")).toBeInTheDocument();
    // error 事件类型标签
    const errorTypeBadges = screen.getAllByText("error");
    expect(errorTypeBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("supports expand/collapse functionality", () => {
    render(<TraceTree spans={mockSpans} />);

    // 初始状态下，前两层应该展开
    expect(screen.getByText("Model Request")).toBeInTheDocument();
    expect(screen.getByText("Tool Call")).toBeInTheDocument();

    // 点击折叠按钮
    const expandButton = screen.getByText("Agent Start").closest("button");
    fireEvent.click(expandButton!);

    // 子节点应该隐藏
    expect(screen.queryByText("Model Request")).not.toBeInTheDocument();
    expect(screen.queryByText("Tool Call")).not.toBeInTheDocument();

    // 再次点击展开
    fireEvent.click(expandButton!);

    // 子节点应该重新显示
    expect(screen.getByText("Model Request")).toBeInTheDocument();
    expect(screen.getByText("Tool Call")).toBeInTheDocument();
  });

  it("handles spans without optional fields", () => {
    const minimalSpans: TraceSpan[] = [
      {
        id: "span-1",
        name: "Minimal Span",
      },
    ];

    render(<TraceTree spans={minimalSpans} />);
    expect(screen.getByText("Minimal Span")).toBeInTheDocument();
  });

  it("renders multiple root spans", () => {
    const rootSpans: TraceSpan[] = [
      {
        id: "root-1",
        name: "Root 1",
        event_type: "step",
      },
      {
        id: "root-2",
        name: "Root 2",
        event_type: "step",
      },
    ];

    render(<TraceTree spans={rootSpans} />);
    expect(screen.getByText("Root 1")).toBeInTheDocument();
    expect(screen.getByText("Root 2")).toBeInTheDocument();
  });
});
