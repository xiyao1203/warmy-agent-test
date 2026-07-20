import { render, screen } from "@testing-library/react";
import { Activity } from "lucide-react";
import { describe, expect, it } from "vitest";

import { MetricCard, MetricCardSkeleton, MetricGrid } from "./metric-card";

describe("MetricCard", () => {
  it("renders a semantic state edge metric with a stable action", () => {
    render(
      <MetricCard
        action={<a href="/runs">查看</a>}
        change="+42"
        icon={<Activity aria-hidden="true" />}
        label="全部运行"
        tone="accent"
        value="1,284"
      />,
    );

    const card = screen.getByRole("article", { name: "全部运行" });
    expect(card).toHaveAttribute("data-tone", "accent");
    expect(card).toHaveAttribute("data-interactive", "true");
    expect(screen.getByRole("link", { name: "查看" })).toBeInTheDocument();
    expect(screen.getByText("+42")).toBeInTheDocument();
  });

  it("exposes running and updated states without changing card structure", () => {
    const { rerender } = render(
      <MetricCard
        icon={<Activity aria-hidden="true" />}
        label="运行中"
        state="running"
        tone="info"
        value="12"
      />,
    );

    expect(screen.getByRole("article", { name: "运行中" })).toHaveAttribute(
      "data-state",
      "running",
    );

    rerender(
      <MetricCard
        icon={<Activity aria-hidden="true" />}
        label="通过率"
        state="updated"
        tone="success"
        value="96.4%"
      />,
    );
    expect(screen.getByRole("article", { name: "通过率" })).toHaveAttribute(
      "data-state",
      "updated",
    );
  });

  it("keeps static and disabled metrics non-interactive", () => {
    render(
      <MetricCard
        action={<a href="/runs">不应出现</a>}
        disabled
        icon={<Activity aria-hidden="true" />}
        label="暂无数据"
        tone="neutral"
        value="—"
      />,
    );

    const card = screen.getByRole("article", { name: "暂无数据" });
    expect(card).toHaveAttribute("data-disabled", "true");
    expect(card).toHaveAttribute("data-interactive", "false");
    expect(screen.queryByRole("link", { name: "不应出现" })).toBeNull();
  });

  it("preserves the metric footprint while loading", () => {
    render(
      <MetricGrid>
        <MetricCardSkeleton label="正在加载通过率" />
      </MetricGrid>,
    );

    expect(
      screen.getByRole("article", { name: "正在加载通过率" }),
    ).toHaveAttribute("aria-busy", "true");
  });
});
