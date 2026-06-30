import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { TraceTimeline } from "../trace-timeline";
import type { TraceSpan } from "../trace-timeline";

const mockSpans: TraceSpan[] = [
  {
    id: "span-1",
    name: "root-span",
    startTime: 0,
    duration: 100,
    status: "ok",
    children: [],
  },
  {
    id: "span-2",
    name: "child-span-1",
    startTime: 10,
    duration: 50,
    status: "ok",
    parentId: "span-1",
    children: [],
  },
  {
    id: "span-3",
    name: "child-span-2",
    startTime: 60,
    duration: 30,
    status: "error",
    parentId: "span-1",
    children: [],
  },
];

describe("TraceTimeline", () => {
  it("renders timeline container", () => {
    render(<TraceTimeline spans={mockSpans} />);

    expect(screen.getByText("root-span")).toBeInTheDocument();
  });

  it("renders all span names", () => {
    render(<TraceTimeline spans={mockSpans} />);

    expect(screen.getByText("root-span")).toBeInTheDocument();
    expect(screen.getByText("child-span-1")).toBeInTheDocument();
    expect(screen.getByText("child-span-2")).toBeInTheDocument();
  });

  it("renders empty state when no spans", () => {
    render(<TraceTimeline spans={[]} />);

    expect(screen.getByText("暂无 Trace 数据")).toBeInTheDocument();
  });

  it("highlights error spans", () => {
    render(<TraceTimeline spans={mockSpans} />);

    // 检查错误 span 是否存在错误标签
    expect(screen.getByText("错误")).toBeInTheDocument();
  });

  it("displays span duration", () => {
    render(<TraceTimeline spans={mockSpans} />);

    expect(screen.getAllByText(/100ms/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/50ms/).length).toBeGreaterThan(0);
  });

  it("calls onSpanClick when span is clicked", () => {
    const onSpanClick = vi.fn();
    render(<TraceTimeline onSpanClick={onSpanClick} spans={mockSpans} />);

    fireEvent.click(screen.getByText("root-span"));
    expect(onSpanClick).toHaveBeenCalledWith(mockSpans[0]);
  });

  it("displays total duration", () => {
    render(<TraceTimeline spans={mockSpans} />);

    expect(screen.getByText("总耗时: 100ms")).toBeInTheDocument();
  });
});
