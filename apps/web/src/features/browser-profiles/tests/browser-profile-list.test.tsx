import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BrowserProfileList } from "../browser-profile-list";
import type { BrowserProfile } from "../api";

const profile: BrowserProfile = {
  cdp_endpoint: "",
  cdp_port: 9222,
  created_at: "2026-06-25T10:00:00Z",
  name: "管理员浏览器",
  profile_id: "profile-1",
  project_id: "project-1",
  status: "stopped",
  storage_state_path: "/tmp/state.json",
  target_domain: "app.example.com",
  updated_at: "2026-06-25T10:00:00Z",
  user_data_dir: "/tmp/profile-1",
};

describe("BrowserProfileList", () => {
  it("shows the browser profile workflow and clear links", () => {
    render(<BrowserProfileList profiles={[profile]} projectId="project-1" />);

    expect(
      screen.getByText(
        "新建实例并保存登录态，测试计划选择后，浏览器用例会在运行时复用。",
      ),
    ).toBeVisible();
    expect(screen.getByText("1. 新建实例")).toBeVisible();
    expect(screen.getByText("2. 保存登录态")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /3. 配置测试计划/ }),
    ).toHaveAttribute("href", "/projects/project-1/test-plans");
    expect(
      screen.getByRole("link", { name: /4. 启动测试执行/ }),
    ).toHaveAttribute("href", "/projects/project-1/runs");
    expect(
      screen.getByRole("columnheader", { name: "实例信息" }),
    ).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "下一步" })).toBeVisible();
    expect(screen.getByText("管理员浏览器")).toBeVisible();
    expect(screen.getByText("已登录")).toBeVisible();
    expect(screen.getByRole("link", { name: "去配置" })).toHaveAttribute(
      "href",
      "/projects/project-1/test-plans",
    );
    expect(
      screen.getByRole("button", { name: "管理管理员浏览器" }),
    ).toBeVisible();
  });

  it("guides empty state and creates a browser profile", async () => {
    const onCreate = vi.fn().mockResolvedValue(profile);
    render(
      <BrowserProfileList
        profiles={[]}
        projectId="project-1"
        onCreate={onCreate}
      />,
    );

    expect(screen.getByText("暂无浏览器实例")).toBeVisible();
    expect(screen.getByText(/测试计划的执行配置中选择它/)).toBeVisible();
    fireEvent.click(
      screen.getAllByRole("button", { name: "新建浏览器实例" })[0],
    );
    fireEvent.change(screen.getByLabelText("名称 *"), {
      target: { value: "运营浏览器" },
    });
    fireEvent.change(screen.getByLabelText("目标域名"), {
      target: { value: "ops.example.com" },
    });
    fireEvent.click(
      screen.getAllByRole("button", { name: "新建浏览器实例" }).at(-1)!,
    );

    await waitFor(() => expect(onCreate).toHaveBeenCalledTimes(1));
    expect(onCreate).toHaveBeenCalledWith({
      name: "运营浏览器",
      target_domain: "ops.example.com",
    });
  });
});
