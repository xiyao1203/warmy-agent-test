import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DropdownSelect } from "./dropdown-select";

describe("DropdownSelect", () => {
  it("opens an app-rendered menu below the trigger and selects an option", () => {
    const onChange = vi.fn();

    render(
      <DropdownSelect aria-label="运行状态" onChange={onChange} value="all">
        <option value="all">状态：全部</option>
        <option value="running">运行中</option>
      </DropdownSelect>,
    );

    fireEvent.pointerDown(screen.getByRole("button", { name: "状态：全部" }));
    expect(screen.getByRole("menu")).toHaveAttribute("data-side", "bottom");
    fireEvent.click(screen.getByRole("menuitem", { name: "运行中" }));

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        target: expect.objectContaining({ value: "running" }),
      }),
    );
  });

  it("keeps a hidden select for existing form change handlers", () => {
    const onChange = vi.fn();

    render(
      <DropdownSelect aria-label="测试计划版本" onChange={onChange} value="">
        <option value="">请选择已发布版本</option>
        <option value="version-1">回归计划 v1</option>
      </DropdownSelect>,
    );

    fireEvent.change(screen.getByLabelText("测试计划版本"), {
      target: { value: "version-1" },
    });

    expect(onChange).toHaveBeenCalledTimes(1);
  });
});
