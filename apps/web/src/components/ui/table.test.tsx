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
  it("contains wide list columns in a local horizontal scroller", () => {
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
      "overflow-x-auto",
    );
    expect(screen.getByTestId("compact-table")).toHaveClass(
      "w-full",
      "table-fixed",
    );
  });

  it("left aligns table headers by default for scanability", () => {
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
      "text-left",
    );
  });

  it("left aligns table cells by default for scanability", () => {
    render(
      <Table>
        <TableBody>
          <TableRow>
            <TableCell>值</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    expect(screen.getByRole("cell", { name: "值" })).toHaveClass("text-left");
  });
});
