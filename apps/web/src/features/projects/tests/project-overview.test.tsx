import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

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
        project={{ archived: true, id: "project-1", name: "项目 A" }}
        user={user}
      />,
    );

    expect(screen.getByRole("heading", { name: "项目 A" })).toBeVisible();
    expect(screen.getAllByText("已归档")).toHaveLength(2);
    expect(screen.getAllByText("开发")).toHaveLength(2);
    expect(screen.getByText("2 位成员")).toBeVisible();
    expect(screen.getByText("暂无测试活动")).toBeVisible();
    expect(screen.getByText(/测试资产将在 M2/)).toBeVisible();
  });
});
