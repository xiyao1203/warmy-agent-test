import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AgentDetail } from "../agent-detail";
import { AgentList } from "../agent-list";

const agent = {
  agent_type: "generic_http" as const,
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  description: "用于客服回归",
  id: "agent-1",
  name: "客服 Agent",
  project_id: "project-1",
  updated_at: "2026-06-25T10:00:00Z",
  updated_by: "user-1",
};

const draftVersion = {
  agent_id: agent.id,
  config: { api_url: "https://agent.example.com", timeout: 30 },
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  id: "version-1",
  published_at: null,
  status: "draft" as const,
  updated_at: "2026-06-25T10:00:00Z",
  version_number: 1,
};

describe("AgentList", () => {
  it("renders loading, empty, service and project-isolation states", () => {
    const { rerender } = render(<AgentList loading projectId="project-1" />);
    expect(screen.getByText("正在加载 Agent…")).toBeVisible();

    rerender(<AgentList agents={[]} projectId="project-1" />);
    expect(screen.getByText("暂无 Agent")).toBeVisible();

    rerender(<AgentList error="service" projectId="project-1" />);
    expect(screen.getByText("Agent 列表暂时不可用")).toBeVisible();

    rerender(<AgentList error="not-found" projectId="project-1" />);
    expect(screen.getByText("项目不存在或你无权访问")).toBeVisible();
  });

  it("renders dense rows and creates an agent", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    const onDelete = vi.fn();
    render(
      <AgentList
        agents={[agent]}
        onCreate={onCreate}
        onDelete={onDelete}
        projectId="project-1"
      />,
    );

    expect(screen.getByText("客服 Agent")).toBeVisible();
    expect(screen.getByText("通用 HTTP")).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "智能体信息" }),
    ).toHaveClass("w-[360px]", "pl-16");
    expect(
      screen.getByRole("columnheader", { name: "接入类型" }),
    ).toHaveClass("w-36", "text-center");
    expect(screen.getByRole("columnheader", { name: "更新时间" })).toHaveClass(
      "w-32",
      "text-center",
    );
    expect(screen.getByRole("table")).toHaveClass("w-auto", "table-fixed");
    const actions = screen.getByRole("group", { name: "客服 Agent 操作" });
    expect(actions).toHaveClass("whitespace-nowrap");
    expect(
      screen.getByRole("link", { name: "查看客服 Agent" }),
    ).toHaveAttribute("href", "/projects/project-1/agents/agent-1");
    expect(screen.getByRole("button", { name: "删除客服 Agent" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "创建 Agent" }));
    fireEvent.change(screen.getByLabelText("Agent 名称"), {
      target: { value: "评测 Agent" },
    });
    fireEvent.change(screen.getByLabelText("Agent 类型"), {
      target: { value: "canvas" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存 Agent" }));

    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ agent_type: "canvas", name: "评测 Agent" }),
    );
  });
});

describe("AgentDetail", () => {
  it("renders versions, creates HTTP config and confirms publish", async () => {
    const onCreateVersion = vi.fn().mockResolvedValue(undefined);
    const onPublish = vi.fn().mockResolvedValue(undefined);
    render(
      <AgentDetail
        agent={agent}
        onCreateVersion={onCreateVersion}
        onPublish={onPublish}
        versions={[draftVersion]}
      />,
    );

    expect(screen.getByText("版本 v1")).toBeVisible();
    expect(screen.getByText("草稿")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));
    fireEvent.change(screen.getByLabelText("API 地址"), {
      target: { value: "https://new-agent.example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存版本" }));
    await waitFor(() => expect(onCreateVersion).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole("button", { name: "发布版本 v1" }));
    expect(await screen.findByText("发布后该版本将不可编辑。")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "确认发布" }));
    await waitFor(() => expect(onPublish).toHaveBeenCalledWith("version-1"));
  });

  it("shows published versions as locked without edit actions", () => {
    render(
      <AgentDetail
        agent={agent}
        versions={[
          {
            ...draftVersion,
            published_at: "2026-06-25T11:00:00Z",
            status: "published",
          },
        ]}
      />,
    );

    expect(screen.getByText("已锁定")).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "编辑版本 v1" }),
    ).not.toBeInTheDocument();
  });
});
