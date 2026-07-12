"use client";

import type {
  CreateEnvironmentVersionRequest,
  EnvironmentVersionResponse,
  UpdateEnvironmentVersionRequest,
} from "@warmy/generated-api-client";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { TableActionButton } from "@/components/ui/table-actions";

import type { CredentialBinding } from "./api";

type EnvironmentVersionDialogProps = {
  triggerLabel: string;
  version?: EnvironmentVersionResponse;
  credentials: CredentialBinding[];
  onSubmit:
    | ((payload: CreateEnvironmentVersionRequest) => Promise<void>)
    | ((payload: UpdateEnvironmentVersionRequest) => Promise<void>);
};

type Section = "config" | "credentials" | "sandbox" | "metadata";

const SECTION_LABELS: Record<Section, string> = {
  config: "变量与请求头",
  credentials: "凭证",
  metadata: "说明",
  sandbox: "沙箱参数",
};

const ALL_SECTIONS: Section[] = [
  "config",
  "credentials",
  "sandbox",
  "metadata",
];

export function EnvironmentVersionDialog({
  credentials,
  onSubmit,
  triggerLabel,
  version,
}: EnvironmentVersionDialogProps) {
  const config = (version?.config ?? {}) as Record<string, unknown>;
  const [open, setOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<Section>("config");

  // ── 配置 ──
  const [variableRows, setVariableRows] = useState(
    recordToRows((config.variables ?? {}) as Record<string, unknown>),
  );
  const [headerRows, setHeaderRows] = useState(
    recordToRows((config.headers ?? {}) as Record<string, unknown>),
  );
  const [initialStateRows, setInitialStateRows] = useState(
    recordToRows((config.initial_state ?? {}) as Record<string, unknown>),
  );

  // ── 凭证 ──
  const existingBindings = (config.credential_binding_ids ?? []) as string[];
  const [credentialIds, setCredentialIds] = useState<string[]>([
    ...existingBindings,
  ]);

  // ── 沙箱 ──
  const [sandboxRows, setSandboxRows] = useState(
    recordToRows((config.sandbox ?? {}) as Record<string, unknown>),
  );

  // ── 元数据 ──
  const [description, setDescription] = useState(
    String(config.description ?? ""),
  );
  const [tags, setTags] = useState((config.tags as string[])?.join(", ") ?? "");

  // ── 提交状态 ──
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    setSubmitting(true);
    setError("");
    try {
      const versionConfig: Record<string, unknown> = {
        variables: rowsToRecord(variableRows),
        headers: rowsToRecord(headerRows),
        initial_state: rowsToRecord(initialStateRows, true),
        credential_binding_ids: credentialIds,
        sandbox: rowsToRecord(sandboxRows, true),
        description: description.trim() || undefined,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      };

      if (version) {
        const updatePayload: UpdateEnvironmentVersionRequest = {
          config: versionConfig,
        };
        await (
          onSubmit as (p: UpdateEnvironmentVersionRequest) => Promise<void>
        )(updatePayload);
      } else {
        const createPayload: CreateEnvironmentVersionRequest = {
          config: versionConfig,
        };
        await (
          onSubmit as (p: CreateEnvironmentVersionRequest) => Promise<void>
        )(createPayload);
      }
      setOpen(false);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "保存版本失败，请检查配置后重试。",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const isEditing = version != null;
  const isPublished = version?.status === "published";

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant={version ? "secondary" : "primary"}>
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-auto">
        <DialogTitle>
          {isEditing
            ? isPublished
              ? `环境版本 v${version.version_number}（已发布，只读）`
              : `编辑环境版本 v${version.version_number}`
            : "创建环境版本"}
        </DialogTitle>
        <DialogDescription>
          配置测试执行时的变量、公开请求头、凭证绑定和沙箱参数。
          {isPublished ? " 已发布版本不可修改。" : ""}
        </DialogDescription>

        {/* ── 分段 Tab ── */}
        <div className="mt-4 flex gap-1 border-b border-[var(--hairline)]">
          {ALL_SECTIONS.map((s) => (
            <button
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                activeSection === s
                  ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
              key={s}
              onClick={() => setActiveSection(s)}
              type="button"
            >
              {SECTION_LABELS[s]}
            </button>
          ))}
        </div>

        <div className="mt-4 space-y-4">
          {/* ── 1. 配置 ── */}
          {activeSection === "config" ? (
            <>
              <KeyValueEditor
                addLabel="添加变量"
                disabled={isPublished}
                emptyText="没有环境变量时可以留空。"
                keyPlaceholder="变量名，例如 BASE_URL"
                label="环境变量"
                onChange={setVariableRows}
                rows={variableRows}
                valuePlaceholder="变量值"
              />
              <KeyValueEditor
                addLabel="添加 Header"
                disabled={isPublished}
                emptyText="公开 Header 不包含密钥；密钥请在“凭证”里选择。"
                keyPlaceholder="Header 名称，例如 X-Env"
                label="公开请求头"
                onChange={setHeaderRows}
                rows={headerRows}
                valuePlaceholder="Header 值"
              />
              <KeyValueEditor
                addLabel="添加状态"
                disabled={isPublished}
                emptyText="没有初始业务状态时可以留空。"
                keyPlaceholder="状态名，例如 workspace_id"
                label="初始业务状态"
                onChange={setInitialStateRows}
                rows={initialStateRows}
                valuePlaceholder="状态值"
              />
            </>
          ) : null}

          {/* ── 2. 凭证 ── */}
          {activeSection === "credentials" ? (
            <div>
              <p className="mb-3 text-sm text-[var(--muted)]">
                选择绑定到此环境版本的加密凭证。凭证值不在 API 中返回。
              </p>
              {credentials.length === 0 ? (
                <p className="text-sm text-[var(--muted)]">
                  暂无可用凭证。请先在页面底部创建加密凭证。
                </p>
              ) : (
                <div className="space-y-2">
                  {credentials.map((cred) => (
                    <label
                      className="flex items-center gap-2 rounded border border-[var(--hairline)] p-3 text-sm"
                      key={cred.id}
                    >
                      <input
                        checked={credentialIds.includes(cred.id)}
                        disabled={isPublished}
                        onChange={(event) =>
                          setCredentialIds((current) =>
                            event.target.checked
                              ? [...current, cred.id]
                              : current.filter((id) => id !== cred.id),
                          )
                        }
                        type="checkbox"
                      />
                      <span className="flex-1">{cred.alias}</span>
                      <code className="text-xs text-[var(--muted)]">
                        {cred.masked_hint}
                      </code>
                    </label>
                  ))}
                </div>
              )}
            </div>
          ) : null}

          {/* ── 3. 沙箱 ── */}
          {activeSection === "sandbox" ? (
            <KeyValueEditor
              addLabel="添加沙箱参数"
              disabled={isPublished}
              emptyText="没有沙箱参数时可以留空，平台会使用默认隔离策略。"
              keyPlaceholder="参数名，例如 seed"
              label="沙箱参数"
              onChange={setSandboxRows}
              rows={sandboxRows}
              valuePlaceholder="参数值"
            />
          ) : null}

          {/* ── 4. 元数据 ── */}
          {activeSection === "metadata" ? (
            <>
              <label className="block text-sm font-medium">
                描述（可选）
                <textarea
                  className="mt-1.5 min-h-16 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] p-3 text-sm"
                  disabled={isPublished}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="记录此版本的用途或变更说明"
                  value={description}
                />
              </label>
              <label className="block text-sm font-medium">
                标签（逗号分隔）
                <input
                  className="mt-1.5 h-9 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] px-3 text-sm"
                  disabled={isPublished}
                  onChange={(event) => setTags(event.target.value)}
                  placeholder="例如 staging, production, v2"
                  value={tags}
                />
              </label>
            </>
          ) : null}

          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}

          {/* ── 底部操作栏 ── */}
          <div className="flex items-center justify-between border-t border-[var(--hairline)] pt-4">
            <div className="flex gap-1">
              {ALL_SECTIONS.map((s, i) => (
                <span
                  className={`text-xs ${
                    activeSection === s
                      ? "text-[var(--foreground)]"
                      : "text-[var(--muted)]"
                  }`}
                  key={s}
                >
                  {SECTION_LABELS[s]}
                  {i < ALL_SECTIONS.length - 1 ? " · " : ""}
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setOpen(false)} type="button">
                取消
              </Button>
              {!isPublished ? (
                <Button
                  disabled={submitting}
                  onClick={submit}
                  type="button"
                  variant="primary"
                >
                  {submitting ? "保存中…" : "保存版本"}
                </Button>
              ) : null}
            </div>
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

function formatCellValue(value: unknown) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function parseCellValue(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);
  if (
    (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
    (trimmed.startsWith("[") && trimmed.endsWith("]"))
  ) {
    try {
      return JSON.parse(trimmed) as unknown;
    } catch {
      return trimmed;
    }
  }
  return trimmed;
}

function recordToRows(record: Record<string, unknown>): KeyValueRow[] {
  return Object.entries(record).map(([key, value]) => ({
    id: newId(),
    key,
    value: formatCellValue(value),
  }));
}

function rowsToRecord(rows: KeyValueRow[], structured = false) {
  return rows.reduce<Record<string, unknown>>((result, row) => {
    const key = row.key.trim();
    if (key)
      result[key] = structured ? parseCellValue(row.value) : row.value.trim();
    return result;
  }, {});
}

function KeyValueEditor({
  addLabel,
  disabled,
  emptyText,
  keyPlaceholder,
  label,
  onChange,
  rows,
  valuePlaceholder,
}: {
  addLabel: string;
  disabled?: boolean;
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
        {!disabled ? (
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
        ) : null}
      </div>
      {rows.length ? (
        <div className="space-y-2">
          {rows.map((row) => (
            <div className="grid grid-cols-[1fr_1fr_auto] gap-2" key={row.id}>
              <Input
                aria-label={`${label}名称`}
                disabled={disabled}
                onChange={(event) =>
                  updateRow(row.id, { key: event.target.value })
                }
                placeholder={keyPlaceholder}
                value={row.key}
              />
              <Input
                aria-label={`${label}值`}
                disabled={disabled}
                onChange={(event) =>
                  updateRow(row.id, { value: event.target.value })
                }
                placeholder={valuePlaceholder}
                value={row.value}
              />
              {!disabled ? (
                <TableActionButton
                  onClick={() =>
                    onChange(rows.filter((item) => item.id !== row.id))
                  }
                  label={`删除${label}`}
                  tone="danger"
                >
                  <Trash2 aria-hidden="true" />
                </TableActionButton>
              ) : null}
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
