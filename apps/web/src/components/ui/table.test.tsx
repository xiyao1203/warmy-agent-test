import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./table";

describe("Table", () => {
  it("keeps list columns inside the available width without horizontal scrolling", () => {
    const { container } = render(
      <Table data-testid="compact-table">
        <TableBody>
          <TableRow>
            <TableCell>很长的字段值</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    expect(container.firstElementChild).toHaveClass(
      "min-w-0",
      "overflow-hidden",
    );
    expect(container.firstElementChild).not.toHaveClass("overflow-x-auto");
    expect(screen.getByTestId("compact-table")).toHaveClass(
      "w-full",
      "table-fixed",
    );
  });

  it("centers table headers by default", () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
      </Table>,
    );

    expect(screen.getByRole("columnheader", { name: "操作" })).toHaveClass(
      "text-center",
    );
  });

  it("centers table cells by default", () => {
    render(
      <Table>
        <TableBody>
          <TableRow>
            <TableCell>值</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    expect(screen.getByRole("cell", { name: "值" })).toHaveClass("text-center");
  });
});
