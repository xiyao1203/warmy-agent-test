import { render, screen } from "@testing-library/react";
import { Activity } from "lucide-react";
import { describe, expect, it } from "vitest";

import { ListCard } from "./list-card";

describe("ListCard", () => {
  it("reserves actions and exposes them for hover and keyboard focus", () => {
    render(
      <ul>
        <ListCard
          actions={<button type="button">打开</button>}
          description="最近运行于 2 分钟前"
          icon={<Activity aria-hidden="true" />}
          title="回归测试 Agent"
          tone="info"
        />
      </ul>,
    );

    expect(screen.getByRole("listitem")).toHaveAttribute("data-tone", "info");
    expect(screen.getByTestId("list-card-actions")).toHaveClass(
      "group-focus-within:opacity-100",
    );
    expect(screen.getByRole("button", { name: "打开" })).toBeInTheDocument();
  });
});
