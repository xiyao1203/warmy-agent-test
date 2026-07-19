import { render, screen } from "@testing-library/react";
import { Pencil } from "lucide-react";
import { describe, expect, it } from "vitest";

import { TableActionButton, TableActions } from "./table-actions";

describe("TableActions", () => {
  it("renders compact icon-only actions with an accessible hover label", () => {
    render(
      <TableActions label="项目 A">
        <TableActionButton accessibleLabel="编辑项目 A" label="编辑">
          <Pencil aria-hidden="true" />
        </TableActionButton>
      </TableActions>,
    );

    const button = screen.getByRole("button", { name: "编辑项目 A" });
    expect(button).toHaveClass("size-8", "p-0");
    expect(button).not.toHaveTextContent("编辑");
    expect(screen.getByRole("tooltip")).toHaveAttribute("data-tooltip", "编辑");
    expect(screen.getByRole("tooltip")).toHaveClass("whitespace-nowrap");
  });
});
