import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ExportButton } from "../export-button";
import { ImportDialog } from "../import-dialog";

describe("ImportDialog", () => {
  it("submits selected format and displays line errors", async () => {
    const onImport = vi.fn().mockRejectedValue({
      errors: [{ line: 2, reason: "name is required" }],
    });
    render(<ImportDialog onImport={onImport} />);

    fireEvent.click(screen.getByRole("button", { name: "导入用例" }));
    fireEvent.change(screen.getByLabelText("导入格式"), {
      target: { value: "jsonl" },
    });
    fireEvent.change(screen.getByLabelText("导入内容"), {
      target: { value: '{"name":"valid"}\n{"name":""}' },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始导入" }));

    await waitFor(() =>
      expect(onImport).toHaveBeenCalledWith({
        content: '{"name":"valid"}\n{"name":""}',
        format: "jsonl",
      }),
    );
    expect(await screen.findByText("第 2 行：name is required")).toBeVisible();
  });
});

describe("ExportButton", () => {
  it("exports JSON, JSONL or CSV content", async () => {
    const onExport = vi.fn().mockResolvedValue({
      content: '[{"name":"case"}]',
      format: "json",
    });
    render(<ExportButton onExport={onExport} />);

    fireEvent.change(screen.getByLabelText("导出格式"), {
      target: { value: "csv" },
    });
    fireEvent.click(screen.getByRole("button", { name: "导出用例" }));

    await waitFor(() => expect(onExport).toHaveBeenCalledWith("csv"));
    expect(screen.getByText("导出内容已准备")).toBeVisible();
  });
});
