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
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/uiverse";
import { TableActionButton } from "@/components/ui/table-actions";
import { TruncatedText } from "@/components/ui/truncated-text";

import type { CredentialBinding } from "./api";
import {
  createCredentialBinding,
  listCredentialBindings,
  listEnvironmentVersions,
} from "./api";
import { EnvironmentVersionDialog } from "./environment-version-dialog";
import { EnvironmentCredentialSection as CredentialSection } from "./environment-credential-section";
import { CreateEnvironmentDialog as CreateTemplateDialog } from "./environment-editor";
import { EnvironmentFlowCard as FlowCard } from "./environment-flow";
import { EnvironmentVersionPanel as VersionPanel } from "./environment-version-panel";

export type EnvironmentListProps = {
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
              <TruncatedText className="font-medium">
                {template.name}
              </TruncatedText>
              <TruncatedText className="mt-0.5 text-xs text-[var(--muted)]">
                {template.description || "暂无描述"}
              </TruncatedText>
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
              <TableActionButton
                label={`删除${template.name}`}
                onClick={() => onDelete(template.id)}
                tone="danger"
              >
                <Trash2 aria-hidden="true" />
              </TableActionButton>
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
