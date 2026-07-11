import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  type BrowserProfile,
  listBrowserProfiles,
} from "@/features/browser-profiles/api";
import {
  createCredentialBinding,
  listCredentialBindings,
} from "@/features/environments/api";

import { AgentVersionDialog } from "../agent-version-dialog";

vi.mock("@/features/browser-profiles/api", () => ({
  listBrowserProfiles: vi.fn(),
}));

vi.mock("@/features/environments/api", () => ({
  createCredentialBinding: vi.fn(),
  listCredentialBindings: vi.fn(),
}));

const browserProfile: BrowserProfile = {
  auth_state_status: "ready",
  auth_state_updated_at: "2026-07-09T10:00:00Z",
  auth_state_version: 2,
  created_at: "2026-07-09T10:00:00Z",
  last_login_at: "2026-07-09T10:00:00Z",
  name: "TapNow 已登录态",
  profile_id: "profile-1",
  project_id: "project-1",
  status: "ready",
  target_domain: "app.tapnow.ai",
  updated_at: "2026-07-09T10:00:00Z",
  last_verified_at: "2026-07-09T10:05:00Z",
};

const credential = {
  alias: "TapNow 测试账号",
  id: "credential-1",
  injection_location: "header",
  injection_name: "target_login",
  kind: "custom",
  masked_hint: "••••7890",
  updated_at: "2026-07-09T10:00:00Z",
};

describe("AgentVersionDialog target integration", () => {
  beforeEach(() => {
    vi.mocked(listBrowserProfiles).mockResolvedValue([browserProfile]);
    vi.mocked(listCredentialBindings).mockResolvedValue([credential]);
    vi.mocked(createCredentialBinding).mockResolvedValue(credential);
  });

  it("keeps target onboarding simple and hides advanced plugin details by default", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <AgentVersionDialog
        agentId="agent-1"
        onSubmit={onSubmit}
        projectId="project-1"
        triggerLabel="创建版本"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));

    expect(await screen.findByLabelText("目标地址")).toBeVisible();
    expect(screen.getByLabelText("登录方式")).toBeVisible();
    expect(screen.getByLabelText("测试范围")).toBeVisible();
    expect(screen.queryByLabelText("目标插件")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("API 地址")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("输入框选择器")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("目标地址"), {
      target: { value: "https://app.tapnow.ai/canvas/demo" },
    });
    fireEvent.change(screen.getByLabelText("登录方式"), {
      target: { value: "browser_profile" },
    });
    fireEvent.change(await screen.findByLabelText("浏览器实例"), {
      target: { value: "profile-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存并开始配置测试" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith({
      config: expect.objectContaining({
        api_url: "https://app.tapnow.ai/canvas/demo",
        credential_binding_ids: [],
        plugin_id: "generic-web-agent",
        plugin_version: "1.0.0",
        target_config: expect.objectContaining({
          browser_profile_id: "profile-1",
          entry_url: "https://app.tapnow.ai/canvas/demo",
          login: { strategy: "browser_profile" },
          plugin_id: "generic-web-agent",
          safety_boundaries: expect.objectContaining({
            blocked_actions: expect.arrayContaining([
              "delete",
              "payment",
              "publish",
              "permission_change",
            ]),
            mode: "readonly",
          }),
        }),
        web_url: "https://app.tapnow.ai/canvas/demo",
      }),
    });

    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));
    fireEvent.click(await screen.findByRole("button", { name: "高级设置" }));
    expect(await screen.findByLabelText("目标插件")).toBeVisible();
    expect(screen.getByLabelText("API 地址")).toBeVisible();
    expect(screen.getByLabelText("输入框选择器")).toBeVisible();
  });

  it("creates a write-only login credential without putting password in version config", async () => {
    vi.mocked(listCredentialBindings).mockResolvedValue([]);
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <AgentVersionDialog
        agentId="agent-1"
        onSubmit={onSubmit}
        projectId="project-1"
        triggerLabel="创建版本"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));
    fireEvent.change(await screen.findByLabelText("目标地址"), {
      target: { value: "https://app.tapnow.ai/home" },
    });
    fireEvent.change(screen.getByLabelText("登录方式"), {
      target: { value: "username_password" },
    });
    fireEvent.change(screen.getByLabelText("凭证名称"), {
      target: { value: "TapNow 测试账号" },
    });
    fireEvent.change(screen.getByLabelText("账号"), {
      target: { value: "tapnow-user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("密码"), {
      target: { value: "secret-password-123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存为项目凭证" }));

    await waitFor(() =>
      expect(createCredentialBinding).toHaveBeenCalledTimes(1),
    );
    expect(createCredentialBinding).toHaveBeenCalledWith(
      "project-1",
      expect.objectContaining({
        alias: "TapNow 测试账号",
        injection_location: "header",
        injection_name: "target_login",
        kind: "custom",
        value: expect.stringContaining("secret-password-123"),
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "保存并开始配置测试" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    const versionPayload = JSON.stringify(onSubmit.mock.calls[0][0]);
    expect(versionPayload).toContain("credential-1");
    expect(versionPayload).not.toContain("secret-password-123");
    expect(versionPayload).not.toContain("tapnow-user@example.com");
  });

  it("disables expired browser profiles", async () => {
    vi.mocked(listBrowserProfiles).mockResolvedValue([
      browserProfile,
      {
        ...browserProfile,
        auth_state_status: "expired" as const,
        name: "已过期实例",
        profile_id: "profile-expired",
      },
    ]);
    render(
      <AgentVersionDialog
        agentId="agent-1"
        onSubmit={vi.fn()}
        projectId="project-1"
        triggerLabel="创建版本"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "创建版本" }));
    fireEvent.change(await screen.findByLabelText("登录方式"), {
      target: { value: "browser_profile" },
    });

    const expired = screen.getByRole("option", { name: /已过期实例/ });
    expect(expired).toBeDisabled();
    expect(expired).toHaveTextContent("已过期");
  });
});
