import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RelationshipList } from "../agent-detail-tabs";

describe("agent relationship list", () => {
  it("renders the empty state without placeholder links", () => {
    render(<RelationshipList empty="暂无关联运行。" items={[]} />);

    expect(screen.getByText("暂无关联运行。")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("renders navigable relationship content", () => {
    render(
      <RelationshipList
        empty="暂无关联运行。"
        items={[
          { href: "/projects/p/runs/r", id: "r", label: "运行 r · passed" },
        ]}
      />,
    );

    expect(
      screen.getByRole("link", { name: "运行 r · passed" }),
    ).toHaveAttribute("href", "/projects/p/runs/r");
  });
});
