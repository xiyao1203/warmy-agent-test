import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ResourcePagination } from "./resource-pagination";


describe("ResourcePagination", () => {
  it("renders standard navigation and changes page", () => {
    const onPageChange = vi.fn();

    render(
      <ResourcePagination
        onPageChange={onPageChange}
        onPageSizeChange={vi.fn()}
        page={2}
        pageSize={10}
        total={42}
        totalPages={5}
      />,
    );

    expect(screen.getByText("共 42 条")).toBeInTheDocument();
    expect(screen.getByText("第 2 / 5 页")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "下一页" }));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it("offers only the approved page sizes", () => {
    const onPageSizeChange = vi.fn();

    render(
      <ResourcePagination
        onPageChange={vi.fn()}
        onPageSizeChange={onPageSizeChange}
        page={1}
        pageSize={10}
        total={0}
        totalPages={0}
      />,
    );

    const select = screen.getByRole("combobox", { name: "每页条数" });
    expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
      "10 条/页",
      "20 条/页",
      "50 条/页",
    ]);
    fireEvent.change(select, { target: { value: "20" } });
    expect(onPageSizeChange).toHaveBeenCalledWith(20);
  });
});
