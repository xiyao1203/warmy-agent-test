import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EnvironmentList } from "../environment-list";
import {
  listCredentialBindings,
  listEnvironmentVersions,
  type CredentialBinding,
} from "../api";

vi.mock("../api", () => ({
  createCredentialBinding: vi.fn(),
  listCredentialBindings: vi.fn(),
  listEnvironmentVersions: vi.fn(),
}));

const credential: CredentialBinding = {
  alias: "Staging Token",
  id: "credential-1",
  injection_location: "header",
  injection_name: "Authorization",
  kind: "bearer",
  masked_hint: "****1234",
  updated_at: "2026-06-25T10:00:00Z",
};

const environment = {
  config: {},
  created_at: "2026-06-25T10:00:00Z",
  created_by: "user-1",
  description: "浏览器测试默认环境",
  id: "environment-1",
  name: "Staging 环境",
  project_id: "project-1",
  template_type: "blank" as const,
  updated_at: "2026-06-25T10:00:00Z",
  updated_by: "user-1",
};

describe("EnvironmentList", () => {
  beforeEach(() => {
    vi.mocked(listCredentialBindings).mockResolvedValue([credential]);
    vi.mocked(listEnvironmentVersions).mockResolvedValue([]);
  });

  it("shows an understandable environment credential flow and clear actions", async () => {
    render(
      <EnvironmentList
        environments={[environment]}
        onCreate={vi.fn()}
        onCreateVersion={vi.fn()}
        onDelete={vi.fn()}
        projectId="project-1"
      />,
    );

    expect(
      screen.getByText(
        "先保存凭证，再绑定环境；测试计划选择环境后，执行时自动注入。",
      ),
    ).toBeVisible();
    expect(screen.getByText("1. 添加凭证")).toBeVisible();
    expect(screen.getByText("2. 配置环境")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /3. 配置测试计划/ }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(
      screen.getByRole("link", { name: /4. 查看测试执行/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(
      screen.getByRole("columnheader", { name: "环境信息" }),
    ).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "下一步" })).toBeVisible();
    expect(screen.getByRole("button", { name: "配置环境" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "创建环境模板" })).toBeNull();
    expect(screen.queryByRole("button", { name: "建版" })).toBeNull();

    await waitFor(() => expect(listCredentialBindings).toHaveBeenCalled());
  });

  it("creates an environment with form rows instead of JSON", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(
      <EnvironmentList
        environments={[]}
        onCreate={onCreate}
        projectId="project-1"
      />,
    );

    await screen.findByText(/Staging Token/);
    fireEvent.click(screen.getAllByRole("button", { name: "新建环境" })[0]);
    fireEvent.change(screen.getByLabelText("模板名称"), {
      target: { value: "Staging 环境" },
    });

    fireEvent.click(screen.getByRole("button", { name: "添加变量" }));
    fireEvent.change(screen.getByPlaceholderText("变量名，例如 BASE_URL"), {
      target: { value: "BASE_URL" },
    });
    fireEvent.change(
      screen.getByPlaceholderText("变量值，例如 https://staging.example.com"),
      { target: { value: "https://staging.example.com" } },
    );

    fireEvent.click(screen.getByRole("button", { name: "添加 Header" }));
    fireEvent.change(screen.getByPlaceholderText("Header 名称，例如 X-Env"), {
      target: { value: "X-Env" },
    });
    fireEvent.change(screen.getByPlaceholderText("Header 值"), {
      target: { value: "staging" },
    });

    fireEvent.click(screen.getByRole("checkbox", { name: /Staging Token/ }));
    expect(screen.queryByText(/必须是合法 JSON/)).toBeNull();
    fireEvent.click(
      screen.getAllByRole("button", { name: "新建环境" }).at(-1)!,
    );

    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        config: expect.objectContaining({
          credential_binding_ids: ["credential-1"],
          headers: { "X-Env": "staging" },
          variables: { BASE_URL: "https://staging.example.com" },
        }),
        name: "Staging 环境",
      }),
    );
  });
});
