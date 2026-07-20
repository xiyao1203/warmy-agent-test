import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InlineAlert } from "./inline-alert";

describe("InlineAlert", () => {
  it("renders actionable danger feedback with a semantic edge", () => {
    render(
      <InlineAlert
        action={<button type="button">重试</button>}
        title="运行启动失败"
        tone="danger"
      >
        请检查运行服务后重试。
      </InlineAlert>,
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveAttribute("data-tone", "danger");
    expect(screen.getByText("运行启动失败")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "重试" })).toBeInTheDocument();
  });

  it("uses status semantics for non-urgent information", () => {
    render(
      <InlineAlert title="数据已更新" tone="info">
        当前列表已同步最新结果。
      </InlineAlert>,
    );

    expect(screen.getByRole("status")).toHaveAttribute("data-tone", "info");
  });
});
