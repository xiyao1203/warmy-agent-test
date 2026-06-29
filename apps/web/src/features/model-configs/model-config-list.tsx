"use client";

import type {
  CreateModelConfigRequest,
  ModelConfigResponse,
  ModelDefaultResponse,
  ModelPurpose,
  UpdateModelConfigRequest,
} from "@warmy/generated-api-client";
import {
  CheckCircle2,
  KeyRound,
  Plus,
  Settings2,
  Trash2,
  Wifi,
} from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

type Props = {
  defaults: ModelDefaultResponse[];
  error?: string;
  loading?: boolean;
  models: ModelConfigResponse[];
  onCreate: (value: CreateModelConfigRequest) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onSetDefault: (purpose: ModelPurpose, id: string) => Promise<void>;
  onTestConnection: (id: string) => Promise<{ latency_ms: number }>;
  onUpdate: (id: string, value: UpdateModelConfigRequest) => Promise<void>;
};

const purposes: Array<{
  purpose: ModelPurpose;
  label: string;
  vision: boolean;
}> = [
  { purpose: "test_agent_chat", label: "测试 Agent 对话", vision: false },
  { purpose: "text_judge", label: "文本裁判", vision: false },
  { purpose: "vision_judge", label: "视觉裁判", vision: true },
];

export function ModelConfigList(props: Props) {
  const [editing, setEditing] = useState<
    ModelConfigResponse | null | undefined
  >();
  const [busy, setBusy] = useState<string | null>(null);
  const [connection, setConnection] = useState<Record<string, string>>({});

  if (props.loading) return <PageState title="正在加载模型配置…" />;
  if (props.error)
    return <PageState title="模型配置暂时不可用" detail={props.error} />;

  async function testConnection(id: string) {
    setBusy(`test:${id}`);
    try {
      const result = await props.onTestConnection(id);
      setConnection((current) => ({
        ...current,
        [id]: `连接成功 · ${result.latency_ms} ms`,
      }));
    } catch {
      setConnection((current) => ({
        ...current,
        [id]: "连接失败，请检查地址、模型 ID 和 API Key",
      }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">模型配置</h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            项目成员共享这些模型；API Key 加密保存且不会回显。
          </p>
        </div>
        <Button onClick={() => setEditing(null)} variant="primary">
          <Plus aria-hidden="true" className="size-4" />
          添加模型
        </Button>
      </header>

      <section aria-labelledby="defaults-heading" className="mt-5">
        <div className="mb-3 flex items-center gap-2">
          <Settings2
            aria-hidden="true"
            className="size-4 text-[var(--text-muted)]"
          />
          <h2 className="text-sm font-semibold" id="defaults-heading">
            默认模型
          </h2>
        </div>
        <div className="grid gap-3 lg:grid-cols-3">
          {purposes.map((item) => {
            const selected = props.defaults.find(
              (value) => value.purpose === item.purpose,
            );
            return (
              <label
                className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4"
                key={item.purpose}
              >
                <span className="block text-sm font-medium">{item.label}</span>
                <span className="mt-1 block text-xs text-[var(--text-muted)]">
                  {item.vision
                    ? "用于图片与多模态质量评分"
                    : "用于结构化生成与文本评测"}
                </span>
                <select
                  aria-label={`${item.label}默认模型`}
                  className="mt-3 h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-subtle)]"
                  onChange={(event) =>
                    void props.onSetDefault(item.purpose, event.target.value)
                  }
                  value={selected?.model_config_id ?? ""}
                >
                  <option value="">尚未配置</option>
                  {props.models
                    .filter(
                      (model) =>
                        model.enabled &&
                        (!item.vision || model.supports_vision),
                    )
                    .map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name} · {model.model_name}
                      </option>
                    ))}
                </select>
              </label>
            );
          })}
        </div>
      </section>

      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {props.models.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <KeyRound
              aria-hidden="true"
              className="mx-auto size-8 text-[var(--text-subtle)]"
            />
            <h2 className="mt-3 text-sm font-semibold">还没有可用模型</h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              添加后才能进行 Agent 对话或模型裁判测试。
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-[var(--border)] bg-[var(--surface-subtle)] text-xs text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-2.5">模型</th>
                  <th className="px-4 py-2.5">服务与凭证</th>
                  <th className="px-4 py-2.5">能力</th>
                  <th className="px-4 py-2.5 text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {props.models.map((model) => (
                  <tr key={model.id}>
                    <td className="px-4 py-3">
                      <div className="font-medium">{model.name}</div>
                      <div className="mt-0.5 font-mono text-xs text-[var(--text-muted)]">
                        {model.model_name}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="max-w-64 truncate text-xs">
                        {model.base_url}
                      </div>
                      <div className="mt-1 font-mono text-xs text-[var(--text-muted)]">
                        {model.api_key_hint}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1.5">
                        <Badge>文本</Badge>
                        {model.supports_vision ? (
                          <Badge tone="accent">视觉</Badge>
                        ) : null}
                        <Badge tone={model.enabled ? "success" : "neutral"}>
                          {model.enabled ? "已启用" : "已停用"}
                        </Badge>
                      </div>
                      {connection[model.id] ? (
                        <p className="mt-1.5 text-xs text-[var(--text-muted)]">
                          {connection[model.id]}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1.5">
                        <Button
                          aria-label={`测试 ${model.name} 连接`}
                          loading={busy === `test:${model.id}`}
                          onClick={() => void testConnection(model.id)}
                        >
                          <Wifi className="size-3.5" />
                          测试连接
                        </Button>
                        <Button
                          aria-label={`编辑 ${model.name}`}
                          onClick={() => setEditing(model)}
                        >
                          <Settings2 className="size-3.5" />
                        </Button>
                        <Button
                          aria-label={`删除 ${model.name}`}
                          onClick={() => {
                            if (window.confirm(`确定删除“${model.name}”吗？`))
                              void props.onDelete(model.id);
                          }}
                          variant="danger"
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {editing !== undefined ? (
        <ModelDialog
          model={editing}
          onClose={() => setEditing(undefined)}
          onCreate={props.onCreate}
          onUpdate={props.onUpdate}
        />
      ) : null}
    </div>
  );
}

function ModelDialog({
  model,
  onClose,
  onCreate,
  onUpdate,
}: {
  model: ModelConfigResponse | null;
  onClose: () => void;
  onCreate: Props["onCreate"];
  onUpdate: Props["onUpdate"];
}) {
  const [name, setName] = useState(model?.name ?? "");
  const [baseUrl, setBaseUrl] = useState(model?.base_url ?? "");
  const [modelName, setModelName] = useState(model?.model_name ?? "");
  const [apiKey, setApiKey] = useState("");
  const [vision, setVision] = useState(model?.supports_vision ?? false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setSubmitting(true);
    setError("");
    try {
      if (model) {
        await onUpdate(model.id, {
          name,
          base_url: baseUrl,
          model_name: modelName,
          supports_vision: vision,
          ...(apiKey ? { api_key: apiKey } : {}),
        });
      } else {
        await onCreate({
          name,
          base_url: baseUrl,
          model_name: modelName,
          api_key: apiKey,
          supports_vision: vision,
        });
      }
      onClose();
    } catch {
      setError("保存失败，请检查字段或项目权限。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      open
    >
      <DialogContent>
        <DialogTitle>{model ? "编辑模型" : "添加模型"}</DialogTitle>
        <DialogDescription>
          支持 OpenAI-Compatible Chat Completions 协议。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <Field label="配置名称">
            <Input
              aria-label="配置名称"
              onChange={(e) => setName(e.target.value)}
              value={name}
            />
          </Field>
          <Field label="Base URL">
            <Input
              aria-label="Base URL"
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.example.com/v1"
              value={baseUrl}
            />
          </Field>
          <Field label="模型 ID">
            <Input
              aria-label="模型 ID"
              onChange={(e) => setModelName(e.target.value)}
              placeholder="gpt-4.1-mini"
              value={modelName}
            />
          </Field>
          <Field label="API Key">
            <Input
              aria-label="API Key"
              autoComplete="new-password"
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={model ? "留空以保留现有密钥" : "输入项目模型密钥"}
              type="password"
              value={apiKey}
            />
          </Field>
          <label className="flex items-center gap-2 text-sm">
            <input
              aria-label="支持视觉输入"
              checked={vision}
              onChange={(e) => setVision(e.target.checked)}
              type="checkbox"
            />
            支持视觉输入
          </label>
          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button onClick={onClose}>取消</Button>
            <Button
              disabled={!name || !baseUrl || !modelName || (!model && !apiKey)}
              loading={submitting}
              onClick={() => void submit()}
              variant="primary"
            >
              <CheckCircle2 className="size-4" />
              保存模型
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Field({ children, label }: { children: ReactNode; label: string }) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <span className="mt-1.5 block">{children}</span>
    </label>
  );
}

function PageState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="px-6 py-12">
      <h1 className="text-sm font-semibold">{title}</h1>
      {detail ? (
        <p className="mt-2 text-sm text-[var(--text-muted)]">{detail}</p>
      ) : null}
    </div>
  );
}
