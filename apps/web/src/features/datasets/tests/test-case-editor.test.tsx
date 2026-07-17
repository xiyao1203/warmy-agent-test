import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TestCaseEditor } from "../test-case-editor";

describe("TestCaseEditor", () => {
  it("submits typed input values through the extracted editors and codecs", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TestCaseEditor onSubmit={onSubmit} triggerLabel="新增用例" />);

    fireEvent.click(screen.getByRole("button", { name: "新增用例" }));
    fireEvent.change(screen.getByLabelText("用例名称"), {
      target: { value: "保留布尔输入" },
    });
    fireEvent.click(screen.getByRole("button", { name: "输入数据" }));
    fireEvent.click(screen.getByRole("button", { name: "添加输入字段" }));
    fireEvent.change(screen.getByLabelText("输入数据字段名"), {
      target: { value: "enabled" },
    });
    fireEvent.change(screen.getByLabelText("输入数据字段值"), {
      target: { value: "true" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存草稿" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        execution_mode: "api",
        input: { enabled: true },
        name: "保留布尔输入",
      }),
    );
  });
});
