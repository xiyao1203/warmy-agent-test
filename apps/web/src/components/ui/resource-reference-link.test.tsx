import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResourceReferenceLink } from "./resource-reference-link";

describe("ResourceReferenceLink", () => {
  it("renders an allowlisted internal project link with version metadata", () => {
    render(
      <ResourceReferenceLink
        reference={{
          href: "/projects/project-1/agents/agent-1",
          id: "agent-1",
          name: "结算 Agent",
          resource_type: "agent",
          status: "published",
          version: 3,
        }}
      />,
    );

    expect(screen.getByRole("link", { name: /结算 Agent/ })).toHaveAttribute(
      "href",
      "/projects/project-1/agents/agent-1",
    );
    expect(screen.getByText("v3")).toBeVisible();
  });

  it("never turns an external or script URL into a link", () => {
    render(
      <ResourceReferenceLink
        reference={{
          href: "javascript:alert(1)",
          id: "agent-1",
          name: "不可信引用",
          resource_type: "agent",
        }}
      />,
    );

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText("不可信引用")).toBeVisible();
  });

  it("shows an explicit unavailable state", () => {
    render(<ResourceReferenceLink reference={null} />);
    expect(screen.getByText("暂无数据")).toBeVisible();
  });
});
