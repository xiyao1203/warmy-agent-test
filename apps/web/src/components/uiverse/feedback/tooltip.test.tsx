import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Tooltip } from "./tooltip";

describe("Tooltip", () => {
  it("portals hover content outside overflow-clipping ancestors", () => {
    render(
      <div className="overflow-hidden">
        <Tooltip content="浏览器实例" side="right">
          <button type="button">浏览器实例入口</button>
        </Tooltip>
      </div>,
    );

    const trigger = screen.getByRole("button", { name: "浏览器实例入口" });
    fireEvent.mouseEnter(trigger.parentElement!);

    const tooltip = screen.getByRole("tooltip", { name: "浏览器实例" });
    expect(tooltip.parentElement).toBe(document.body);
    expect(tooltip).toHaveClass("fixed");
    expect(tooltip).toHaveAttribute("data-state", "open");
  });

  it("closes pointer-open content on pointer down", () => {
    render(
      <Tooltip content="切换至深色">
        <button type="button">主题</button>
      </Tooltip>,
    );

    const wrapper = screen.getByRole("button", { name: "主题" }).parentElement!;
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByRole("tooltip")).toHaveAttribute("data-state", "open");

    fireEvent.pointerDown(wrapper);
    expect(screen.getByRole("tooltip")).toHaveAttribute("data-state", "closed");
    expect(screen.getByRole("tooltip")).toBeEmptyDOMElement();

    fireEvent.mouseEnter(wrapper);
    expect(screen.getByRole("tooltip")).toHaveAttribute("data-state", "closed");

    fireEvent.mouseLeave(wrapper);
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByRole("tooltip")).toHaveAttribute("data-state", "open");
  });
});
