import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

import { HelpSearch, type HelpTopic } from "../help-search";

const topics: HelpTopic[] = [
  { id: "1", title: "Agent 管理", description: "创建和管理测试 Agent", href: "#agents", category: "智能体" },
  { id: "2", title: "数据集", description: "创建数据集和测试用例", href: "#datasets", category: "测试资产" },
  { id: "3", title: "测试计划", description: "配置和运行测试计划", href: "#test-plans", category: "测试执行" },
];

describe("HelpSearch", () => {
  it("renders all topics when no search query", () => {
    render(<HelpSearch topics={topics} />);

    expect(screen.getByText("Agent 管理")).toBeInTheDocument();
    expect(screen.getByText("数据集")).toBeInTheDocument();
    expect(screen.getByText("测试计划")).toBeInTheDocument();
  });

  it("filters topics based on search query", () => {
    render(<HelpSearch topics={topics} />);

    const searchInput = screen.getByRole("searchbox");
    fireEvent.change(searchInput, { target: { value: "Agent" } });

    expect(screen.getByText("Agent 管理")).toBeInTheDocument();
    expect(screen.queryByText("数据集")).not.toBeInTheDocument();
    expect(screen.queryByText("测试计划")).not.toBeInTheDocument();
  });

  it("shows empty state when no topics match", () => {
    render(<HelpSearch topics={topics} />);

    const searchInput = screen.getByRole("searchbox");
    fireEvent.change(searchInput, { target: { value: "不存在的内容" } });

    expect(screen.getByText("没有找到相关内容")).toBeInTheDocument();
  });

  it("clears search when clicking clear button", () => {
    render(<HelpSearch topics={topics} />);

    const searchInput = screen.getByRole("searchbox");
    fireEvent.change(searchInput, { target: { value: "Agent" } });

    const clearButton = screen.getByLabelText("清空搜索");
    fireEvent.click(clearButton);

    expect(searchInput).toHaveValue("");
    expect(screen.getByText("数据集")).toBeInTheDocument();
  });

  it("filters topics by category", () => {
    render(<HelpSearch topics={topics} />);

    const searchInput = screen.getByRole("searchbox");
    fireEvent.change(searchInput, { target: { value: "智能体" } });

    expect(screen.getByText("Agent 管理")).toBeInTheDocument();
    expect(screen.queryByText("数据集")).not.toBeInTheDocument();
  });
});
