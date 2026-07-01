"use client";

import type {
  CreateEnvironmentTemplateRequest,
  EnvironmentTemplateResponse,
} from "@warmy/generated-api-client";
import { Cog, Plus } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/uiverse";

import type { CredentialBinding } from "./api";
import { createCredentialBinding, listCredentialBindings } from "./api";

type EnvironmentListProps = {
  environments?: EnvironmentTemplateResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateEnvironmentTemplateRequest) => Promise<unknown>;
  onDelete?: (templateId: string) => Promise<unknown>;
  projectId: string;
};

const typeLabels: Record<string, string> = {
  blank: "空环境",
  preset: "预设",
};

export function EnvironmentList({
  environments = [],
  error,
  loading = false,
  onCreate,
  onDelete,
  projectId,
}: EnvironmentListProps) {
  const [credentials, setCredentials] = useState<CredentialBinding[]>([]);
  useEffect(() => {
    void listCredentialBindings(projectId)
      .then(setCredentials)
      .catch(() => setCredentials([]));
  }, [projectId]);
  if (loading) {
    return <EnvironmentListSkeleton />;
  }
  if (error === "not-found") {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        <p className="text-[var(--text-muted)]">项目不存在或无权访问</p>
      </div>
    );
  }
  if (error === "service") {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        <p className="text-[var(--text-muted)]">环境模板列表暂时不可用</p>
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">环境与凭证</h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            管理测试环境模板、测试凭证、Mock 服务和沙箱配置。
          </p>
        </div>
        {onCreate && (
          <CreateTemplateDialog credentials={credentials} onCreate={onCreate} />
        )}
      </header>

      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        {!environments.length ? (
          <EmptyState
            description="创建环境模板后，可在测试计划中引用并自动配置执行环境。"
            title="暂无环境模板"
          />
        ) : (
          <Table className="w-auto min-w-[680px] table-fixed">
            <TableHeader className="bg-[var(--surface-subtle)]">
              <TableRow>
                <TableHead className="w-[420px]">模板信息</TableHead>
                <TableHead className="w-32 text-center">类型</TableHead>
                <TableHead className="w-32 text-center">更新时间</TableHead>
                <TableHead className="w-24 text-center">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {environments.map((template) => (
                <TableRow
                  className="transition-colors hover:bg-[var(--surface-subtle)]"
                  key={template.id}
                >
                  <TableCell>
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-sm)] bg-[var(--surface-subtle)]">
                        <Cog aria-hidden="true" className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-medium">{template.name}</p>
                        <p className="mt-0.5 truncate text-xs text-[var(--text-muted)]">
                          {template.description || "暂无描述"}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge
                      tone={
                        template.template_type === "preset"
                          ? "accent"
                          : "neutral"
                      }
                    >
                      {typeLabels[template.template_type] ??
                        template.template_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-center text-sm text-[var(--text-muted)]">
                    {new Date(template.updated_at).toLocaleDateString("zh-CN")}
                  </TableCell>
                  <TableCell className="text-center">
                    {onDelete && (
                      <Button
                        aria-label={`删除${template.name}`}
                        onClick={() => onDelete(template.id)}
                        variant="danger"
                      >
                        删除
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>
      <CredentialSection
        credentials={credentials}
        onCreate={async (payload) => {
          const created = await createCredentialBinding(projectId, payload);
          setCredentials((current) => [created, ...current]);
        }}
      />
    </div>
  );
}

function CredentialSection({
  credentials,
  onCreate,
}: {
  credentials: CredentialBinding[];
  onCreate: (payload: {
    alias: string;
    kind: string;
    injection_location: string;
    injection_name: string;
    value: string;
  }) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [alias, setAlias] = useState("");
  const [name, setName] = useState("Authorization");
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  return (
    <section className="mt-6 rounded border border-[var(--border)] bg-[var(--surface)] p-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold">加密凭证绑定</h2>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            密钥仅加密保存；列表和 API 永不返回明文。
          </p>
        </div>
        <Button onClick={() => setOpen(true)} variant="secondary">
          新增凭证
        </Button>
      </div>
      <ul className="mt-4 space-y-2 text-sm">
        {credentials.map((item) => (
          <li
            className="flex justify-between rounded border border-[var(--border)] p-3"
            key={item.id}
          >
            <span>
              {item.alias} · {item.injection_location}:{item.injection_name}
            </span>
            <code>{item.masked_hint}</code>
          </li>
        ))}
      </ul>
      <Dialog onOpenChange={setOpen} open={open}>
        <DialogContent>
          <DialogTitle>新增加密凭证</DialogTitle>
          <DialogDescription>
            凭证值保存后不可读取，只能替换。
          </DialogDescription>
          <div className="mt-4 space-y-3">
            <Input
              onChange={(event) => setAlias(event.target.value)}
              placeholder="别名，如 staging-token"
              value={alias}
            />
            <Input
              onChange={(event) => setName(event.target.value)}
              placeholder="Header 名称"
              value={name}
            />
            <Input
              onChange={(event) => setValue(event.target.value)}
              placeholder="凭证值"
              type="password"
              value={value}
            />
            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
            <div className="flex justify-end gap-2">
              <Button onClick={() => setOpen(false)}>取消</Button>
              <Button
                onClick={async () => {
                  try {
                    await onCreate({
                      alias,
                      kind: "bearer",
                      injection_location: "header",
                      injection_name: name,
                      value,
                    });
                    setOpen(false);
                    setAlias("");
                    setValue("");
                  } catch (caught) {
                    setError(
                      caught instanceof Error ? caught.message : "保存失败",
                    );
                  }
                }}
                variant="primary"
              >
                保存
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}

function CreateTemplateDialog({
  credentials,
  onCreate,
}: {
  credentials: CredentialBinding[];
  onCreate: (payload: CreateEnvironmentTemplateRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [variables, setVariables] = useState("{}");
  const [headers, setHeaders] = useState("{}");
  const [initialState, setInitialState] = useState("{}");
  const [credentialIds, setCredentialIds] = useState<string[]>([]);

  async function submit() {
    if (!name.trim()) {
      setError("请输入模板名称");
      return;
    }
    setSubmitting(true);
    try {
      const parsedVariables = JSON.parse(variables) as Record<string, unknown>;
      const parsedHeaders = JSON.parse(headers) as Record<string, unknown>;
      const parsedInitialState = JSON.parse(initialState) as Record<
        string,
        unknown
      >;
      await onCreate({
        config: {
          variables: parsedVariables,
          headers: parsedHeaders,
          initial_state: parsedInitialState,
          credential_binding_ids: credentialIds,
          sandbox: {},
        },
        description: description.trim() || null,
        name: name.trim(),
        template_type: "blank",
      });
      setOpen(false);
      setName("");
      setDescription("");
      setError("");
    } catch (caught) {
      setError(
        caught instanceof SyntaxError
          ? "变量、Headers 和初始状态必须是合法 JSON 对象。"
          : "创建失败，请检查输入后重试。",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建环境模板
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建环境模板</DialogTitle>
        <DialogDescription>
          环境模板用于定义测试执行时的初始配置，可在测试计划中引用。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            模板名称
            <Input
              className="mt-1.5"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="block text-sm font-medium">
            描述
            <Input
              className="mt-1.5"
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </label>
          <JsonField
            label="环境变量（JSON）"
            onChange={setVariables}
            value={variables}
          />
          <div>
            <p className="text-sm font-medium">凭证绑定</p>
            <div className="mt-2 space-y-2">
              {credentials.map((credential) => (
                <label
                  className="flex items-center gap-2 text-sm"
                  key={credential.id}
                >
                  <input
                    checked={credentialIds.includes(credential.id)}
                    onChange={(event) =>
                      setCredentialIds((current) =>
                        event.target.checked
                          ? [...current, credential.id]
                          : current.filter((id) => id !== credential.id),
                      )
                    }
                    type="checkbox"
                  />
                  {credential.alias} · {credential.masked_hint}
                </label>
              ))}
            </div>
          </div>
          <JsonField
            label="公开 Headers（JSON）"
            onChange={setHeaders}
            value={headers}
          />
          <JsonField
            label="初始状态（JSON）"
            onChange={setInitialState}
            value={initialState}
          />
          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button
              disabled={submitting}
              onClick={() => setOpen(false)}
              type="button"
            >
              取消
            </Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              type="button"
              variant="primary"
            >
              创建模板
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function JsonField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <textarea
        className="mt-1.5 min-h-20 w-full rounded border border-[var(--border)] bg-[var(--surface)] p-3 font-mono text-xs"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      />
    </label>
  );
}

function EnvironmentListSkeleton() {
  return (
    <div className="min-w-0 px-6 py-6">
      {/* Header skeleton */}
      <header className="flex items-start justify-between gap-4 border-b border-[var(--border)] pb-5">
        <div>
          <Skeleton className="h-8 w-40" />
          <Skeleton className="mt-2 h-4 w-56" />
        </div>
        <Skeleton className="h-9 w-28" />
      </header>

      {/* Table skeleton */}
      <section className="mt-5 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="p-4">
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="ml-auto h-4 w-16" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
