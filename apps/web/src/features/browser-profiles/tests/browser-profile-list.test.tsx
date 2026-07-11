import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BrowserProfileList } from "../browser-profile-list";
import type { BrowserProfile } from "../api";

const profile: BrowserProfile = {
  auth_state_status: "ready",
  auth_state_updated_at: "2026-07-04T10:00:00Z",
  auth_state_version: 1,
  created_at: "2026-06-25T10:00:00Z",
  name: "管理员浏览器",
  profile_id: "profile-1",
  project_id: "project-1",
  status: "stopped",
  target_domain: "app.example.com",
  updated_at: "2026-06-25T10:00:00Z",
  last_login_at: "2026-07-04T10:00:00Z",
  last_verified_at: "2026-07-04T10:05:00Z",
};

const runningProfile: BrowserProfile = {
  ...profile,
  auth_state_status: "missing",
  auth_state_updated_at: null,
  auth_state_version: 0,
  last_login_at: "",
  last_verified_at: null,
  status: "running",
};

describe("BrowserProfileList", () => {
  it("shows the browser profile workflow and clear links", async () => {
    render(<BrowserProfileList profiles={[profile]} projectId="project-1" />);

    expect(
      screen.getByText(/新建实例后启动浏览器，人工登录并确认保存/),
    ).toBeVisible();
    expect(screen.getByText("1. 新建实例")).toBeVisible();
    expect(screen.getByText("2. 启动并登录")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /3. 配置测试计划/ }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(
      screen.getByRole("link", { name: /4. 启动测试执行/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(screen.getByRole("columnheader", { name: "实例" })).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "操作" })).toBeVisible();
    expect(screen.getByText("这些实例用在哪儿")).toBeVisible();
    expect(screen.getByText(/Worker 通过短期租约恢复登录态/)).toBeVisible();
    expect(screen.getByText("管理员浏览器")).toBeVisible();
    expect(screen.getByText("登录态可用")).toBeVisible();
    expect(screen.getByRole("button", { name: "启动并登录" })).toHaveClass(
      "shrink-0",
      "whitespace-nowrap",
    );
    expect(
      screen.getByRole("button", { name: "管理管理员浏览器" }),
    ).toHaveClass("shrink-0");
    fireEvent.pointerDown(
      screen.getByRole("button", { name: "管理管理员浏览器" }),
    );
    expect(
      await screen.findByRole("menuitem", { name: "配置计划" }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(screen.getByRole("menuitem", { name: "设置实例" })).toBeVisible();
    expect(screen.getByRole("menuitem", { name: "删除实例" })).toBeVisible();
    expect(document.querySelector("table")?.className).not.toContain("min-w");
  });

  it("guides empty state, creates a browser profile and starts login", async () => {
    const onCreate = vi.fn().mockResolvedValue(profile);
    const onStart = vi.fn().mockResolvedValue(runningProfile);
    render(
      <BrowserProfileList
        profiles={[]}
        projectId="project-1"
        onCreate={onCreate}
        onStart={onStart}
      />,
    );

    expect(screen.getByText("暂无浏览器实例")).toBeVisible();
    expect(screen.getByText(/启动浏览器完成登录/)).toBeVisible();
    fireEvent.click(
      screen.getAllByRole("button", { name: "新建浏览器实例" })[0],
    );
    fireEvent.change(screen.getByLabelText("名称 *"), {
      target: { value: "运营浏览器" },
    });
    fireEvent.change(screen.getByLabelText("目标域名"), {
      target: { value: "ops.example.com" },
    });
    fireEvent.change(screen.getByLabelText("登录地址"), {
      target: { value: "https://ops.example.com/login" },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建并启动登录" }));

    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
    expect(onCreate).toHaveBeenCalledWith({
      name: "运营浏览器",
      target_domain: "ops.example.com",
    });
    expect(onStart).toHaveBeenCalledWith("profile-1", {
      login_url: "https://ops.example.com/login",
    });
  });

  it("completes login, stops and deletes from visible row actions", async () => {
    const onCompleteLogin = vi.fn().mockResolvedValue(profile);
    const onStop = vi.fn().mockResolvedValue(profile);
    const onDelete = vi.fn().mockResolvedValue(undefined);
    render(
      <BrowserProfileList
        profiles={[runningProfile]}
        projectId="project-1"
        onCompleteLogin={onCompleteLogin}
        onDelete={onDelete}
        onStop={onStop}
      />,
    );

    expect(screen.getByText("登录中")).toBeVisible();
    expect(screen.getByRole("button", { name: "我已完成登录" })).toHaveClass(
      "shrink-0",
      "whitespace-nowrap",
    );
    fireEvent.click(screen.getByRole("button", { name: "我已完成登录" }));
    await waitFor(() =>
      expect(onCompleteLogin).toHaveBeenCalledWith("profile-1", {
        stop_after_save: true,
      }),
    );

    fireEvent.pointerDown(
      screen.getByRole("button", { name: "管理管理员浏览器" }),
    );
    fireEvent.click(await screen.findByRole("menuitem", { name: "删除实例" }));
    fireEvent.click(screen.getByRole("button", { name: "删除" }));
    await waitFor(() => expect(onDelete).toHaveBeenCalledWith("profile-1"));
  });

  it("verifies a saved auth state and shows expired state without exposing paths", async () => {
    const onVerify = vi.fn().mockResolvedValue(profile);
    const { rerender } = render(
      <BrowserProfileList
        profiles={[profile]}
        projectId="project-1"
        onVerify={onVerify}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "验证登录态" }));
    await waitFor(() => expect(onVerify).toHaveBeenCalledWith("profile-1"));
    expect(
      screen.queryByText(/\/tmp|storage_state|9222/),
    ).not.toBeInTheDocument();

    rerender(
      <BrowserProfileList
        profiles={[{ ...profile, auth_state_status: "expired" }]}
        projectId="project-1"
      />,
    );
    expect(screen.getByText("登录态已过期")).toBeVisible();
  });
});
