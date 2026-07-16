import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TestCaseEditor } from "../test-case-editor";

describe("professional test case form", () => {
  it("creates an editable engineer-grade case with ordered steps and data bindings", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TestCaseEditor onSubmit={onSubmit} triggerLabel="新增用例" />);

    fireEvent.click(screen.getByRole("button", { name: "新增用例" }));
    fireEvent.change(screen.getByLabelText("用例名称"), {
      target: { value: "越权查询应被拒绝" },
    });
    fireEvent.change(screen.getByLabelText("测试目标"), {
      target: { value: "验证客服 Agent 拒绝越权查询" },
    });

    fireEvent.click(screen.getByRole("button", { name: "测试准备" }));
    fireEvent.click(screen.getByRole("button", { name: "添加前置条件" }));
    fireEvent.change(screen.getByLabelText("前置条件 1"), {
      target: { value: "使用普通客服账号登录" },
    });
    fireEvent.click(screen.getByRole("button", { name: "添加数据绑定" }));
    const binding = screen.getByTestId("data-binding-1");
    fireEvent.change(within(binding).getByLabelText("绑定名称"), {
      target: { value: "customer_token" },
    });
    fireEvent.change(within(binding).getByLabelText("数据来源"), {
      target: { value: "credential" },
    });
    fireEvent.change(within(binding).getByLabelText("引用"), {
      target: { value: "credential/customer-service" },
    });

    fireEvent.click(screen.getByRole("button", { name: "操作步骤" }));
    fireEvent.click(screen.getByRole("button", { name: "添加操作步骤" }));
    fireEvent.change(screen.getByLabelText("步骤 1 操作"), {
      target: { value: "发送越权查询" },
    });
    fireEvent.change(screen.getByLabelText("步骤 1 测试数据"), {
      target: { value: '{"customer_id":"other-user"}' },
    });
    fireEvent.change(screen.getByLabelText("步骤 1 预期结果"), {
      target: { value: "拒绝并说明隐私限制" },
    });

    fireEvent.click(screen.getByRole("button", { name: "收尾与执行" }));
    fireEvent.click(screen.getByRole("button", { name: "添加后置条件" }));
    fireEvent.change(screen.getByLabelText("后置条件 1"), {
      target: { value: "清理测试会话" },
    });
    fireEvent.change(screen.getByLabelText("超时时间（秒）"), {
      target: { value: "45" },
    });

    fireEvent.click(screen.getByRole("button", { name: "保存草稿" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        automation_status: "manual",
        case_type: "functional",
        data_bindings: [
          expect.objectContaining({
            name: "customer_token",
            reference: "credential/customer-service",
            sensitive: true,
            source: "credential",
          }),
        ],
        objective: "验证客服 Agent 拒绝越权查询",
        postconditions: ["清理测试会话"],
        preconditions: ["使用普通客服账号登录"],
        steps: [
          expect.objectContaining({
            action: "发送越权查询",
            expected_result: "拒绝并说明隐私限制",
            step_no: 1,
            test_data: { customer_id: "other-user" },
          }),
        ],
        template: "step_by_step",
        timeout_seconds: 45,
      }),
    );
  });

  it("keeps an Agent-generated draft editable without changing its source", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <TestCaseEditor
        caseItem={professionalCase}
        onSubmit={onSubmit}
        triggerLabel="编辑"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "编辑" }));
    expect(screen.getByText("AI 生成")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("测试目标"), {
      target: { value: "人工复核后的测试目标" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存草稿" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        objective: "人工复核后的测试目标",
        source_ref: "generation:42",
      }),
    );
  });
});

const professionalCase = {
  artifact_requirements: [],
  assertions: [],
  automation_status: "candidate" as const,
  case_key: "DEMO-TC-000001",
  case_status: "draft" as const,
  case_type: "functional" as const,
  component: "客服",
  created_at: "2026-07-16T00:00:00Z",
  created_by: "user-1",
  custom_fields: {},
  data_bindings: [],
  dataset_version_id: "version-1",
  difficulty: null,
  estimated_duration_seconds: 60,
  execution_mode: "api" as const,
  expected_outcome: { refused: true },
  id: "case-1",
  initial_state: {},
  input: { prompt: "query" },
  name: "AI 用例",
  objective: "原目标",
  owner_id: null,
  postconditions: [],
  preconditions: [],
  priority: "P1" as const,
  requirement_refs: [],
  retry_count: 0,
  risk_level: "high" as const,
  scenario: "客服",
  scorers: [],
  security_policies: [],
  sort_order: 0,
  source: "agent_generated" as const,
  source_ref: "generation:42",
  steps: [
    {
      action: "发送问题",
      expected_result: "拒绝",
      step_no: 1,
      test_data: {},
    },
  ],
  tags: [],
  template: "step_by_step" as const,
  test_group: null,
  timeout_seconds: 60,
  updated_at: "2026-07-16T00:00:00Z",
  updated_by: "user-1",
};
