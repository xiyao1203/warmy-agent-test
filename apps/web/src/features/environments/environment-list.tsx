"use client";

import type {
  CreateEnvironmentTemplateRequest,
  CreateEnvironmentVersionRequest,
  EnvironmentTemplateResponse,
  EnvironmentVersionResponse,
  UpdateEnvironmentVersionRequest,
} from "@warmy/generated-api-client";
import {
  ClipboardCheck,
  Cog,
  KeyRound,
  PlayCircle,
  Plus,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
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
        <p className="text-[var(--muted)]">项目不存在或无权访问</p>
      </div>
    );
  }
  if (error === "service") {
    return (
      <div className="grid min-h-[calc(100vh-3rem)] place-items-center text-sm">
        <p className="text-[var(--muted)]">环境模板列表暂时不可用</p>
      </div>
    );
  }

  return (
    <div className="min-w-0 px-6 py-6">
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">环境与凭证</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            先保存凭证，再绑定环境；测试计划选择环境后，执行时自动注入。
          </p>
        </div>
        {onCreate && (
          <CreateTemplateDialog credentials={credentials} onCreate={onCreate} />
        )}
      </header>

      <section className="mt-5 grid gap-3 md:grid-cols-4">
        <FlowCard
          description="明文只保存一次"
          icon={<KeyRound aria-hidden="true" className="size-4" />}
          label="1. 添加凭证"
        />
        <FlowCard
          description="绑定变量和凭证"
          icon={<ShieldCheck aria-hidden="true" className="size-4" />}
          label="2. 配置环境"
        />
        <FlowCard
          description="选择已发布环境"
          href={`/projects/${projectId}/test-plans`}
          icon={<ClipboardCheck aria-hidden="true" className="size-4" />}
          label="3. 配置测试计划"
        />
        <FlowCard
          description="执行时自动注入"
          href={`/projects/${projectId}/runs`}
          icon={<PlayCircle aria-hidden="true" className="size-4" />}
          label="4. 查看测试执行"
        />
      </section>

      <section className="mt-5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        {!environments.length ? (
          <EmptyState
            action={
              onCreate ? (
                <CreateTemplateDialog
                  credentials={credentials}
                  onCreate={onCreate}
                />
              ) : null
            }
            description="新建环境后，发布版本即可在测试计划中选择。"
            title="暂无环境模板"
          />
        ) : (
          <Table className="w-full table-fixed">
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="w-[34%]">环境信息</TableHead>
                <TableHead className="w-[12%]">类型</TableHead>
                <TableHead className="w-[16%]">版本</TableHead>
                <TableHead className="w-[16%]">更新时间</TableHead>
                <TableHead className="w-[22%]">下一步</TableHead>
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

function FlowCard({
  description,
  href,
  icon,
  label,
}: {
  description: string;
  href?: string;
  icon: ReactNode;
  label: string;
}) {
  const content = (
    <>
      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)]">
        {icon}
      </span>
      <span className="min-w-0">
        <span className="block font-medium">{label}</span>
        <span className="block truncate text-xs text-[var(--muted)]">
          {description}
        </span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link
        className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm transition-colors hover:border-[var(--primary)]"
        href={href}
      >
        {content}
      </Link>
    );
  }

  return (
    <div className="flex min-w-0 items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 text-sm">
      {content}
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
      <TableRow className="transition-colors hover:bg-[var(--canvas-soft)]">
        <TableCell>
          <div className="mx-auto flex w-fit min-w-0 items-center gap-3 text-left">
            <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--canvas-soft)]">
              <Cog aria-hidden="true" className="size-4" />
            </span>
            <div className="min-w-0">
              <p className="truncate font-medium">{template.name}</p>
              <p className="mt-0.5 truncate text-xs text-[var(--muted)]">
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
            className="text-sm font-medium text-[var(--primary)] hover:underline"
            onClick={handleToggleVersions}
            type="button"
          >
            {versionsLoaded ? `${versions.length} 个版本` : "查看版本"}
          </button>
        </TableCell>
        <TableCell className="whitespace-nowrap text-center text-sm text-[var(--muted)]">
          {new Date(template.updated_at).toLocaleDateString("zh-CN")}
        </TableCell>
        <TableCell className="text-center">
          <div className="flex items-center justify-center gap-1">
            {onCreateVersion ? (
              <EnvironmentVersionDialog
                credentials={credentials}
                triggerLabel="配置环境"
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
    <div className="rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-4 text-sm">
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
        <p className="text-[var(--muted)]">
          尚无版本。点击上方按钮创建第一个版本。
        </p>
      ) : (
        <div className="space-y-2">
          {versions.map((v) => (
            <div
              className="flex items-center justify-between rounded border border-[var(--hairline)] bg-[var(--surface)] p-3"
              key={v.id}
            >
              <div className="flex items-center gap-3">
                <Badge tone={v.status === "published" ? "accent" : "neutral"}>
                  v{v.version_number}
                </Badge>
                <Badge tone={v.status === "published" ? "accent" : "neutral"}>
                  {v.status === "published" ? "已发布" : "草稿"}
                </Badge>
                <span className="text-xs text-[var(--muted)]">
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
    <section className="mt-6 rounded border border-[var(--hairline)] bg-[var(--surface)] p-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold">凭证库</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">
            添加后可绑定到环境，测试执行时按 Header 自动注入；列表和 API
            永不返回明文。
          </p>
        </div>
        <Button onClick={() => setOpen(true)} variant="secondary">
          添加凭证
        </Button>
      </div>
      {credentials.length ? (
        <ul className="mt-4 space-y-2 text-sm">
          {credentials.map((item) => (
            <li
              className="flex justify-between rounded border border-[var(--hairline)] p-3"
              key={item.id}
            >
              <span>
                {item.alias} · {item.injection_location}:{item.injection_name}
              </span>
              <code>{item.masked_hint}</code>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 rounded border border-dashed border-[var(--hairline)] p-4 text-sm text-[var(--muted)]">
          暂无凭证。添加一次后，在新建环境或配置环境时勾选即可。
        </p>
      )}
      <Dialog onOpenChange={setOpen} open={open}>
        <DialogContent>
          <DialogTitle>添加凭证</DialogTitle>
          <DialogDescription>
            凭证值保存后不可读取，只会在测试执行时注入。
          </DialogDescription>
          <div className="mt-4 space-y-3">
            <label className="block text-sm font-medium">
              凭证名称
              <Input
                className="mt-1.5"
                onChange={(event) => setAlias(event.target.value)}
                placeholder="例如 Staging API Token"
                value={alias}
              />
            </label>
            <label className="block text-sm font-medium">
              注入到哪个 Header
              <Input
                className="mt-1.5"
                onChange={(event) => setName(event.target.value)}
                placeholder="例如 Authorization"
                value={name}
              />
            </label>
            <label className="block text-sm font-medium">
              凭证值
              <Input
                className="mt-1.5"
                onChange={(event) => setValue(event.target.value)}
                placeholder="只保存一次，之后不可查看明文"
                type="password"
                value={value}
              />
            </label>
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
  const [variableRows, setVariableRows] = useState<KeyValueRow[]>([]);
  const [headerRows, setHeaderRows] = useState<KeyValueRow[]>([]);
  const [initialStateRows, setInitialStateRows] = useState<KeyValueRow[]>([]);
  const [credentialIds, setCredentialIds] = useState<string[]>([]);

  async function submit() {
    if (!name.trim()) {
      setError("请输入模板名称");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({
        config: {
          variables: rowsToRecord(variableRows),
          headers: rowsToRecord(headerRows),
          initial_state: rowsToRecord(initialStateRows),
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
      setVariableRows([]);
      setHeaderRows([]);
      setInitialStateRows([]);
      setCredentialIds([]);
      setError("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
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
          新建环境
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>新建环境</DialogTitle>
        <DialogDescription>
          新建后可绑定凭证并发布版本，测试计划会选择已发布环境执行。
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
          <KeyValueEditor
            addLabel="添加变量"
            emptyText="没有环境变量时可以留空。"
            keyPlaceholder="变量名，例如 BASE_URL"
            label="环境变量"
            onChange={setVariableRows}
            rows={variableRows}
            valuePlaceholder="变量值，例如 https://staging.example.com"
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
              {!credentials.length ? (
                <p className="text-sm text-[var(--muted)]">
                  还没有凭证。可以先创建环境，稍后再配置环境时绑定凭证。
                </p>
              ) : null}
            </div>
          </div>
          <KeyValueEditor
            addLabel="添加 Header"
            emptyText="公开 Header 不包含密钥；密钥请使用上方凭证绑定。"
            keyPlaceholder="Header 名称，例如 X-Env"
            label="公开请求头"
            onChange={setHeaderRows}
            rows={headerRows}
            valuePlaceholder="Header 值"
          />
          <KeyValueEditor
            addLabel="添加状态"
            emptyText="没有初始业务状态时可以留空。"
            keyPlaceholder="状态名，例如 workspace_id"
            label="初始业务状态"
            onChange={setInitialStateRows}
            rows={initialStateRows}
            valuePlaceholder="状态值"
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
              新建环境
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

type KeyValueRow = { id: string; key: string; value: string };

function newId() {
  return Math.random().toString(36).slice(2, 10);
}

function rowsToRecord(rows: KeyValueRow[]) {
  return rows.reduce<Record<string, string>>((result, row) => {
    const key = row.key.trim();
    if (key) result[key] = row.value.trim();
    return result;
  }, {});
}

function KeyValueEditor({
  addLabel,
  emptyText,
  keyPlaceholder,
  label,
  onChange,
  rows,
  valuePlaceholder,
}: {
  addLabel: string;
  emptyText: string;
  keyPlaceholder: string;
  label: string;
  onChange: (rows: KeyValueRow[]) => void;
  rows: KeyValueRow[];
  valuePlaceholder: string;
}) {
  function updateRow(id: string, patch: Partial<KeyValueRow>) {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-sm font-medium">{label}</p>
        <Button
          className="h-8 px-2 text-xs"
          onClick={() =>
            onChange([...rows, { id: newId(), key: "", value: "" }])
          }
          type="button"
          variant="secondary"
        >
          <Plus aria-hidden="true" className="mr-1 size-3.5" />
          {addLabel}
        </Button>
      </div>
      {rows.length ? (
        <div className="space-y-2">
          {rows.map((row) => (
            <div className="grid grid-cols-[1fr_1fr_auto] gap-2" key={row.id}>
              <Input
                aria-label={`${label}名称`}
                onChange={(event) =>
                  updateRow(row.id, { key: event.target.value })
                }
                placeholder={keyPlaceholder}
                value={row.key}
              />
              <Input
                aria-label={`${label}值`}
                onChange={(event) =>
                  updateRow(row.id, { value: event.target.value })
                }
                placeholder={valuePlaceholder}
                value={row.value}
              />
              <Button
                aria-label={`删除${label}`}
                onClick={() =>
                  onChange(rows.filter((item) => item.id !== row.id))
                }
                type="button"
                variant="danger"
              >
                删除
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <p className="rounded border border-dashed border-[var(--hairline)] p-3 text-sm text-[var(--muted)]">
          {emptyText}
        </p>
      )}
    </div>
  );
}

function EnvironmentListSkeleton() {
  return (
    <div className="min-w-0 px-6 py-6">
      {/* Header skeleton */}
      <header className="flex items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <Skeleton className="h-8 w-40" />
          <Skeleton className="mt-2 h-4 w-56" />
        </div>
        <Skeleton className="h-9 w-28" />
      </header>

      {/* Table skeleton */}
      <section className="mt-5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
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
