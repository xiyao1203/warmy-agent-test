import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ExportButton } from "../export-button";
import { ImportDialog } from "../import-dialog";
import { ImportWizard } from "../import-wizard";
import { buildTestCaseTemplate } from "../test-case-format";

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

  it("shows the platform standard template requirements", () => {
    render(<ImportDialog onImport={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "导入用例" }));

    expect(screen.getByText("中文导入模板")).toBeVisible();
    expect(screen.getByText("必填：用例名称、输入、执行模式")).toBeVisible();
    expect(screen.getByText(/风险等级：严重、高、中、低/)).toBeVisible();
  });
});

describe("ImportWizard", () => {
  it("offers standard templates that match the create case fields", () => {
    const jsonTemplate = JSON.parse(buildTestCaseTemplate("json")) as Array<
      Record<string, unknown>
    >;

    expect(jsonTemplate[0]).toEqual(
      expect.objectContaining({
        用例名称: expect.any(String),
        输入: expect.any(Object),
        执行模式: "API",
        初始状态: expect.any(Object),
        期望结果: expect.any(Object),
        断言规则: expect.any(Array),
        评分器: expect.any(Array),
        安全策略: expect.any(Array),
        标签: expect.any(Array),
        业务场景: expect.any(String),
        优先级: "P1",
        风险等级: "低",
        难度: "简单",
        测试分组: "测试集",
      }),
    );

    expect(buildTestCaseTemplate("csv").split("\n")[0]).toBe(
      "用例名称,输入,执行模式,初始状态,期望结果,断言规则,评分器,安全策略,标签,业务场景,优先级,风险等级,难度,测试分组",
    );

    render(<ImportWizard />);
    fireEvent.click(screen.getByRole("button", { name: "导入" }));

    expect(screen.getByText("下载中文导入模板")).toBeVisible();
    expect(screen.getByText("必填：用例名称、输入、执行模式")).toBeVisible();
    expect(screen.getByText(/测试分组：训练集、验证集、测试集/)).toBeVisible();
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
