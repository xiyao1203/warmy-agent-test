import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableValue,
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
      "table-auto",
    );
  });

  it("centers table headers and cells by default", () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>值</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    expect(screen.getByRole("columnheader", { name: "操作" })).toHaveClass(
      "text-center",
    );
    expect(screen.getByRole("cell", { name: "值" })).toHaveClass("text-center");
  });

  it("uses the shared table header and body typography roles", () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>模型</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>gpt-5.5</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    expect(screen.getByRole("columnheader", { name: "模型" })).toHaveClass(
      "text-table-head",
    );
    expect(screen.getByRole("cell", { name: "gpt-5.5" })).toHaveClass(
      "text-table-cell",
    );
  });

  it("centers a rich value block while keeping its text readable", () => {
    render(
      <TableValue data-testid="table-value">
        <strong>资源名称</strong>
        <p>资源说明</p>
      </TableValue>,
    );

    expect(screen.getByTestId("table-value")).toHaveClass(
      "mx-auto",
      "w-fit",
      "max-w-full",
      "text-left",
    );
  });
});
