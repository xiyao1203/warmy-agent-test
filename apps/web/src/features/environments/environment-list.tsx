"use client";

import type {
  CreateEnvironmentTemplateRequest,
  CreateEnvironmentVersionRequest,
  EnvironmentTemplateResponse,
  EnvironmentVersionResponse,
  UpdateEnvironmentVersionRequest,
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
import {
  createCredentialBinding,
  listCredentialBindings,
  listEnvironmentVersions,
} from "./api";
import { EnvironmentVersionDialog } from "./environment-version-dialog";

type EnvironmentListProps = {
  environments?: EnvironmentTemplateResponse[];
  error?: "not-found" | "service";
  loading?: boolean;
  onCreate?: (payload: CreateEnvironmentTemplateRequest) => Promise<unknown>;
  onDelete?: (templateId: string) => Promise<unknown>;
  onCreateVersion?: (
    templateId: string,
    payload: CreateEnvironmentVersionRequest,
  ) => Promise<EnvironmentVersionResponse>;
  onUpdateVersion?: (
    templateId: string,
    versionId: string,
    payload: UpdateEnvironmentVersionRequest,
  ) => Promise<EnvironmentVersionResponse>;
  onPublishVersion?: (
    templateId: string,
    versionId: string,
  ) => Promise<EnvironmentVersionResponse>;
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
  onCreateVersion,
  onDelete,
  onPublishVersion,
  onUpdateVersion,
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
                <TableHead className="w-[380px]">模板信息</TableHead>
                <TableHead className="w-24 text-center">类型</TableHead>
                <TableHead className="w-24 text-center">版本</TableHead>
                <TableHead className="w-32 text-center">更新时间</TableHead>
                <TableHead className="w-24 text-center">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {environments.map((template) => (
                <TemplateRow
                  credentials={credentials}
                  key={template.id}
                  onCreateVersion={onCreateVersion}
                  onPublishVersion={onPublishVersion}
                  onUpdateVersion={onUpdateVersion}
                  projectId={projectId}
                  template={template}
                  onDelete={onDelete}
                />
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

function TemplateRow({
  credentials,
  onCreateVersion,
  onDelete,
  onPublishVersion,
  onUpdateVersion,
  projectId,
  template,
}: {
  credentials: CredentialBinding[];
  onCreateVersion?: EnvironmentListProps["onCreateVersion"];
  onDelete?: (templateId: string) => Promise<unknown>;
  onPublishVersion?: EnvironmentListProps["onPublishVersion"];
  onUpdateVersion?: EnvironmentListProps["onUpdateVersion"];
  projectId: string;
  template: EnvironmentTemplateResponse;
}) {
  const [versions, setVersions] = useState<EnvironmentVersionResponse[]>([]);
  const [versionsLoaded, setVersionsLoaded] = useState(false);
  const [showVersions, setShowVersions] = useState(false);

  async function loadVersions() {
    if (versionsLoaded) return;
    try {
      const items = await listEnvironmentVersions(projectId, template.id);
      setVersions(items);
    } catch {
      // versions unavailable
    }
    setVersionsLoaded(true);
  }

  async function handleToggleVersions() {
    if (!showVersions) {
      await loadVersions();
    }
    setShowVersions((prev) => !prev);
  }

  const draftVersion = versions.find((v) => v.status === "draft");
  const publishedCount = versions.filter(
    (v) => v.status === "published",
  ).length;

  return (
    <>
      <TableRow className="transition-colors hover:bg-[var(--surface-subtle)]">
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
            tone={template.template_type === "preset" ? "accent" : "neutral"}
          >
            {typeLabels[template.template_type] ?? template.template_type}
          </Badge>
        </TableCell>
        <TableCell className="text-center">
          <button
            className="text-sm font-medium text-[var(--accent)] hover:underline"
            onClick={handleToggleVersions}
            type="button"
          >
            {versionsLoaded ? versions.length : "…"}
          </button>
        </TableCell>
        <TableCell className="whitespace-nowrap text-center text-sm text-[var(--text-muted)]">
          {new Date(template.updated_at).toLocaleDateString("zh-CN")}
        </TableCell>
        <TableCell className="text-center">
          <div className="flex items-center justify-center gap-1">
            {onCreateVersion ? (
              <EnvironmentVersionDialog
                credentials={credentials}
                triggerLabel="创建版本"
                onSubmit={async (payload: CreateEnvironmentVersionRequest) => {
                  const result = await onCreateVersion(template.id, payload);
                  setVersions((prev) => [result, ...prev]);
                }}
                version={draftVersion}
              />
            ) : null}
            {onDelete ? (
              <Button
                aria-label={`删除${template.name}`}
                onClick={() => onDelete(template.id)}
                variant="danger"
              >
                删除
              </Button>
            ) : null}
          </div>
        </TableCell>
      </TableRow>

      {/* Version detail panel */}
      {showVersions ? (
        <TableRow>
          <TableCell colSpan={5}>
            <VersionPanel
              credentials={credentials}
              draftVersion={draftVersion}
              onCreateVersion={onCreateVersion}
              onPublishVersion={onPublishVersion}
              onUpdateVersion={onUpdateVersion}
              publishedCount={publishedCount}
              template={template}
              versions={versions}
            />
          </TableCell>
        </TableRow>
      ) : null}
    </>
  );
}

function VersionPanel({
  credentials,
  draftVersion,
  onCreateVersion,
  onPublishVersion,
  onUpdateVersion,
  publishedCount,
  template,
  versions,
}: {
  credentials: CredentialBinding[];
  draftVersion?: EnvironmentVersionResponse;
  onCreateVersion?: EnvironmentListProps["onCreateVersion"];
  onPublishVersion?: EnvironmentListProps["onPublishVersion"];
  onUpdateVersion?: EnvironmentListProps["onUpdateVersion"];
  publishedCount: number;
  template: EnvironmentTemplateResponse;
  versions: EnvironmentVersionResponse[];
}) {
  return (
    <div className="rounded border border-[var(--border)] bg-[var(--surface-subtle)] p-4 text-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">
          版本历史 · {publishedCount} 个已发布
          {draftVersion ? " · 1 个草稿" : ""}
        </h3>
        {onCreateVersion ? (
          <EnvironmentVersionDialog
            credentials={credentials}
            key={draftVersion?.id ?? "new"}
            triggerLabel={draftVersion ? "编辑草稿" : "创建版本"}
            version={draftVersion}
            onSubmit={
              draftVersion
                ? async (payload: UpdateEnvironmentVersionRequest) => {
                    if (onUpdateVersion) {
                      await onUpdateVersion(
                        template.id,
                        draftVersion.id,
                        payload as UpdateEnvironmentVersionRequest,
                      );
                    }
                  }
                : async (payload: CreateEnvironmentVersionRequest) => {
                    if (onCreateVersion) {
                      await onCreateVersion(template.id, payload);
                    }
                  }
            }
          />
        ) : null}
      </div>

      {versions.length === 0 ? (
        <p className="text-[var(--text-muted)]">
          尚无版本。点击上方按钮创建第一个版本。
        </p>
      ) : (
        <div className="space-y-2">
          {versions.map((v) => (
            <div
              className="flex items-center justify-between rounded border border-[var(--border)] bg-[var(--surface)] p-3"
              key={v.id}
            >
              <div className="flex items-center gap-3">
                <Badge tone={v.status === "published" ? "accent" : "neutral"}>
                  v{v.version_number}
                </Badge>
                <Badge tone={v.status === "published" ? "accent" : "neutral"}>
                  {v.status === "published" ? "已发布" : "草稿"}
                </Badge>
                <span className="text-xs text-[var(--text-muted)]">
                  {new Date(v.updated_at).toLocaleDateString("zh-CN")}
                </span>
              </div>
              <div className="flex gap-1">
                {v.status === "draft" && onUpdateVersion ? (
                  <EnvironmentVersionDialog
                    credentials={credentials}
                    triggerLabel="编辑"
                    version={v}
                    onSubmit={async (
                      payload: UpdateEnvironmentVersionRequest,
                    ) => {
                      if (onUpdateVersion) {
                        await onUpdateVersion(
                          template.id,
                          v.id,
                          payload as UpdateEnvironmentVersionRequest,
                        );
                      }
                    }}
                  />
                ) : null}
                {v.status === "draft" && onPublishVersion ? (
                  <Button
                    onClick={async () => {
                      if (onPublishVersion) {
                        await onPublishVersion(template.id, v.id);
                      }
                    }}
                    variant="primary"
                  >
                    发布
                  </Button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
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
