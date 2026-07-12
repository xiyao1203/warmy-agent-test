import { render, screen } from "@testing-library/react";
import { Pencil } from "lucide-react";
import { describe, expect, it } from "vitest";

import { TableActionButton, TableActions } from "./table-actions";

describe("TableActions", () => {
  it("renders compact icon-only actions with an accessible hover label", () => {
    render(
      <TableActions label="项目 A">
        <TableActionButton label="编辑项目 A">
          <Pencil aria-hidden="true" />
        </TableActionButton>
      </TableActions>,
    );

    const button = screen.getByRole("button", { name: "编辑项目 A" });
    expect(button).toHaveClass("size-8", "p-0");
    expect(button).not.toHaveTextContent("编辑项目 A");
    expect(screen.getByRole("tooltip")).toHaveAttribute(
      "data-tooltip",
      "编辑项目 A",
    );
  });
});
