"use client";

import type {
  CreateEnvironmentVersionRequest,
  EnvironmentVersionResponse,
  UpdateEnvironmentVersionRequest,
} from "@warmy/generated-api-client";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

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
  config: "配置",
  credentials: "凭证",
  metadata: "元数据",
  sandbox: "沙箱",
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
  const [variables, setVariables] = useState(
    JSON.stringify(config.variables ?? {}, null, 2),
  );
  const [headers, setHeaders] = useState(
    JSON.stringify(config.headers ?? {}, null, 2),
  );
  const [initialState, setInitialState] = useState(
    JSON.stringify(config.initial_state ?? {}, null, 2),
  );

  // ── 凭证 ──
  const existingBindings = (config.credential_binding_ids ?? []) as string[];
  const [credentialIds, setCredentialIds] = useState<string[]>([
    ...existingBindings,
  ]);

  // ── 沙箱 ──
  const [sandboxConfig, setSandboxConfig] = useState(
    JSON.stringify(config.sandbox ?? {}, null, 2),
  );

  // ── 元数据 ──
  const [description, setDescription] = useState(
    String(config.description ?? ""),
  );
  const [tags, setTags] = useState((config.tags as string[])?.join(", ") ?? "");

  // ── 提交状态 ──
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function parseJson(
    raw: string,
    label: string,
  ): Record<string, unknown> | null {
    try {
      const parsed = JSON.parse(raw) as unknown;
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        setError(`${label} 必须是 JSON 对象`);
        return null;
      }
      return parsed as Record<string, unknown>;
    } catch {
      setError(`${label} 不是合法 JSON`);
      return null;
    }
  }

  async function submit() {
    const parsedVariables = parseJson(variables, "环境变量");
    if (parsedVariables === null) return;
    const parsedHeaders = parseJson(headers, "公开 Headers");
    if (parsedHeaders === null) return;
    const parsedInitialState = parseJson(initialState, "初始状态");
    if (parsedInitialState === null) return;
    const parsedSandbox = parseJson(sandboxConfig, "沙箱配置");
    if (parsedSandbox === null) return;

    setSubmitting(true);
    setError("");
    try {
      const versionConfig: Record<string, unknown> = {
        variables: parsedVariables,
        headers: parsedHeaders,
        initial_state: parsedInitialState,
        credential_binding_ids: credentialIds,
        sandbox: parsedSandbox,
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
          配置测试执行时的环境变量、凭证绑定、沙箱和元数据。
          {isPublished ? " 已发布版本不可修改。" : ""}
        </DialogDescription>

        {/* ── 分段 Tab ── */}
        <div className="mt-4 flex gap-1 border-b border-[var(--border)]">
          {ALL_SECTIONS.map((s) => (
            <button
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                activeSection === s
                  ? "border-b-2 border-[var(--accent)] text-[var(--accent)]"
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
              <JsonField
                disabled={isPublished}
                label="环境变量（JSON）"
                onChange={setVariables}
                value={variables}
              />
              <JsonField
                disabled={isPublished}
                label="公开 Headers（JSON）"
                onChange={setHeaders}
                value={headers}
              />
              <JsonField
                disabled={isPublished}
                label="初始状态（JSON）"
                onChange={setInitialState}
                value={initialState}
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
                      className="flex items-center gap-2 rounded border border-[var(--border)] p-3 text-sm"
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
            <JsonField
              disabled={isPublished}
              label="沙箱配置（JSON）"
              onChange={setSandboxConfig}
              value={sandboxConfig}
            />
          ) : null}

          {/* ── 4. 元数据 ── */}
          {activeSection === "metadata" ? (
            <>
              <label className="block text-sm font-medium">
                描述（可选）
                <textarea
                  className="mt-1.5 min-h-16 w-full rounded border border-[var(--border)] bg-[var(--surface)] p-3 text-sm"
                  disabled={isPublished}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="记录此版本的用途或变更说明"
                  value={description}
                />
              </label>
              <label className="block text-sm font-medium">
                标签（逗号分隔）
                <input
                  className="mt-1.5 h-9 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3 text-sm"
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
          <div className="flex items-center justify-between border-t border-[var(--border)] pt-4">
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

function JsonField({
  disabled,
  label,
  onChange,
  value,
}: {
  disabled?: boolean;
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <textarea
        className="mt-1.5 min-h-24 w-full rounded border border-[var(--border)] bg-[var(--surface)] p-3 font-mono text-xs"
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        value={value}
      />
    </label>
  );
}
