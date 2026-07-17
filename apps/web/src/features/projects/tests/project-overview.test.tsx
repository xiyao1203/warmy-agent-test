import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { projectFixture } from "@/test/fixtures";

import { ProjectOverview } from "../project-overview";

const user = {
  display_name: "Jason",
  email: "jason@example.com",
  id: "user-1",
  must_change_password: false,
  role: "developer" as const,
  status: "active" as const,
};

describe("ProjectOverview", () => {
  it("shows a loading state", () => {
    render(<ProjectOverview loading user={user} />);
    expect(screen.getByText("正在加载项目概览…")).toBeVisible();
  });

  it("uses one neutral state for missing or inaccessible projects", () => {
    render(<ProjectOverview error="not-found" user={user} />);
    expect(screen.getByText("项目不存在或你无权访问")).toBeVisible();
  });

  it("shows a retryable service error", () => {
    render(<ProjectOverview error="service" user={user} />);
    expect(screen.getByText("项目概览暂时不可用")).toBeVisible();
  });

  it("shows archived state, membership and honest empty activity", () => {
    render(
      <ProjectOverview
        members={[
          { role: "developer", user_id: "user-1" },
          { role: "viewer", user_id: "user-2" },
        ]}
        assetSummary={{ agents: 2, datasets: 3, testPlans: 1 }}
        project={projectFixture({ archived: true, status: "archived" })}
        user={user}
      />,
    );

    expect(screen.getByRole("heading", { name: "项目 A" })).toBeVisible();
    expect(screen.getAllByText("已归档")).toHaveLength(2);
    expect(screen.getAllByText("开发")).toHaveLength(2);
    expect(screen.getAllByText("2 位成员")).toHaveLength(2);
    expect(screen.getByText("2 Agents")).toBeVisible();
    expect(screen.getByText("3 数据集")).toBeVisible();
    expect(screen.getByText("1 测试计划")).toBeVisible();
    expect(screen.getByText("查看运行中心")).toBeVisible();
    expect(
      screen.getByText(
        "当前概览页只展示项目摘要；完整运行记录、进度与结果在运行中心统一查看。",
      ),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "去运行中心" })).toHaveAttribute(
      "href",
      "/projects/project-1/runs",
    );
  });

  it("shows compact empty member guidance", () => {
    render(
      <ProjectOverview
        members={[]}
        project={projectFixture()}
        user={{ ...user, role: "super_admin" }}
      />,
    );

    expect(screen.getByText("暂无普通成员")).toBeVisible();
    expect(screen.getByText("暂无项目成员")).toBeVisible();
    expect(
      screen.getByText(/需要协作时可到系统用户和项目成员配置中分配权限/),
    ).toBeVisible();
  });
});
