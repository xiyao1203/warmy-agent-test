import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { listBrowserProfiles } from "@/features/browser-profiles/api";
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

const browserProfile = {
  cdp_endpoint: "http://127.0.0.1:9222",
  cdp_port: 9222,
  created_at: "2026-07-09T10:00:00Z",
  last_login_at: "2026-07-09T10:00:00Z",
  name: "TapNow 已登录态",
  profile_id: "profile-1",
  project_id: "project-1",
  status: "ready",
  storage_state_path: "s3://profiles/profile-1.json",
  target_domain: "app.tapnow.ai",
  updated_at: "2026-07-09T10:00:00Z",
  user_data_dir: "/tmp/profile-1",
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

  it("builds a visual target plugin config from target URL and credential binding", async () => {
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

    fireEvent.change(await screen.findByLabelText("目标插件"), {
      target: { value: "tapnow-canvas-agent" },
    });
    fireEvent.change(screen.getByLabelText("目标访问地址"), {
      target: { value: "https://app.tapnow.ai/canvas/demo" },
    });
    fireEvent.change(screen.getByLabelText("登录方式"), {
      target: { value: "credential" },
    });
    fireEvent.change(await screen.findByLabelText("项目凭证"), {
      target: { value: "credential-1" },
    });
    fireEvent.change(await screen.findByLabelText("浏览器实例"), {
      target: { value: "profile-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存版本" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith({
      config: expect.objectContaining({
        api_url: "https://app.tapnow.ai/canvas/demo",
        credential_binding_ids: ["credential-1"],
        plugin_id: "tapnow-canvas-agent",
        plugin_version: "1.0.0",
        target_config: expect.objectContaining({
          browser_profile_id: "profile-1",
          entry_url: "https://app.tapnow.ai/canvas/demo",
          login: {
            credential_binding_id: "credential-1",
            strategy: "credential",
          },
          plugin_id: "tapnow-canvas-agent",
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
    fireEvent.change(await screen.findByLabelText("目标访问地址"), {
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

    fireEvent.click(screen.getByRole("button", { name: "保存版本" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    const versionPayload = JSON.stringify(onSubmit.mock.calls[0][0]);
    expect(versionPayload).toContain("credential-1");
    expect(versionPayload).not.toContain("secret-password-123");
    expect(versionPayload).not.toContain("tapnow-user@example.com");
  });
});
