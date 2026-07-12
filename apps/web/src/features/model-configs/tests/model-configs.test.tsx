import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ModelConfigList } from "../model-config-list";

const model = {
  id: "model-1",
  name: "主模型",
  provider_type: "openai_compatible",
  base_url: "https://api.example.com/v1",
  model_name: "model-a",
  supports_text: true,
  supports_vision: true,
  enabled: true,
  has_api_key: true,
  api_key_hint: "...cret",
  created_at: "2026-06-29T10:00:00Z",
  updated_at: "2026-06-29T10:00:00Z",
};

describe("ModelConfigList", () => {
  it("renders defaults and never exposes a plaintext key", () => {
    render(
      <ModelConfigList
        defaults={[
          {
            purpose: "test_agent_chat",
            model_config_id: "model-1",
            updated_at: "now",
          },
        ]}
        models={[model]}
        onCreate={vi.fn()}
        onDelete={vi.fn()}
        onSetDefault={vi.fn()}
        onTestConnection={vi.fn()}
        onUpdate={vi.fn()}
      />,
    );
    expect(screen.getByText("主模型")).toBeVisible();
    expect(screen.getByText("...cret")).toBeVisible();
    expect(screen.getByText("测试 Agent 对话")).toBeVisible();
    expect(screen.queryByText("sk-production-secret")).not.toBeInTheDocument();
    expect(screen.getByText("模型").closest("th")).toHaveClass("w-[27%]");
    expect(screen.getByText("服务与凭证").closest("th")).toHaveClass("w-[35%]");
    expect(screen.getByText("能力").closest("th")).toHaveClass("w-[23%]");
    expect(screen.getByText("操作").closest("th")).toHaveClass("w-[15%]");
    expect(screen.getByRole("table")).toHaveClass("w-full", "table-fixed");
    for (const label of ["测试 主模型 连接", "编辑 主模型", "删除 主模型"]) {
      const action = screen.getByRole("button", { name: label });
      expect(action).toHaveClass("size-8", "p-0");
      expect(action).not.toHaveTextContent(/测试连接|编辑|删除/);
    }
  });

  it("creates a fully configured model", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(
      <ModelConfigList
        defaults={[]}
        models={[]}
        onCreate={onCreate}
        onDelete={vi.fn()}
        onSetDefault={vi.fn()}
        onTestConnection={vi.fn()}
        onUpdate={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "添加模型" }));
    fireEvent.change(screen.getByLabelText("配置名称"), {
      target: { value: "DeepSeek" },
    });
    fireEvent.change(screen.getByLabelText("Base URL"), {
      target: { value: "https://api.deepseek.com/v1" },
    });
    fireEvent.change(screen.getByLabelText("模型 ID"), {
      target: { value: "deepseek-chat" },
    });
    fireEvent.change(screen.getByLabelText("API Key"), {
      target: { value: "sk-secret" },
    });
    fireEvent.click(screen.getByLabelText("支持视觉输入"));
    fireEvent.click(screen.getByRole("button", { name: "保存模型" }));
    await waitFor(() =>
      expect(onCreate).toHaveBeenCalledWith({
        name: "DeepSeek",
        base_url: "https://api.deepseek.com/v1",
        model_name: "deepseek-chat",
        api_key: "sk-secret",
        supports_vision: true,
      }),
    );
  });

  it("shows the server problem detail when saving fails", async () => {
    const onCreate = vi
      .fn()
      .mockRejectedValue({ detail: "部署未配置模型凭证主密钥", status: 503 });
    render(
      <ModelConfigList
        defaults={[]}
        models={[]}
        onCreate={onCreate}
        onDelete={vi.fn()}
        onSetDefault={vi.fn()}
        onTestConnection={vi.fn()}
        onUpdate={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "添加模型" }));
    fireEvent.change(screen.getByLabelText("配置名称"), {
      target: { value: "主模型" },
    });
    fireEvent.change(screen.getByLabelText("Base URL"), {
      target: { value: "https://api.example.com/v1" },
    });
    fireEvent.change(screen.getByLabelText("模型 ID"), {
      target: { value: "model-a" },
    });
    fireEvent.change(screen.getByLabelText("API Key"), {
      target: { value: "secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "保存模型" }));

    expect(await screen.findByText("部署未配置模型凭证主密钥")).toBeVisible();
  });
});
