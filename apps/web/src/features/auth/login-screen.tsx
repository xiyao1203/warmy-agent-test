"use client";

import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Database,
  FlaskConical,
  PlayCircle,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { BrandMark } from "@/components/layout/brand-mark";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { listProjects } from "@/features/projects";

import { getCurrentUser } from "./api";
import {
  hasProjectScopedReturnTo,
  resolveLoginDestinationFromProjects,
} from "./login-destination";
import { LoginForm } from "./login-form";

const EVIDENCE_STEPS = [
  {
    icon: <Bot aria-hidden="true" />,
    label: "测试 Agent",
    text: "把需求生成可编辑用例",
    state: "已同步",
  },
  {
    icon: <Database aria-hidden="true" />,
    label: "用例库",
    text: "断言、输入和评分保持一致",
    state: "128 条",
  },
  {
    icon: <PlayCircle aria-hidden="true" />,
    label: "运行中心",
    text: "API 与浏览器执行沉淀证据",
    state: "运行中",
  },
  {
    icon: <ShieldCheck aria-hidden="true" />,
    label: "发布门禁",
    text: "审核、安全与质量结论可追溯",
    state: "风险低",
  },
] as const;

export function LoginScreen({ returnTo }: { returnTo?: string }) {
  const router = useRouter();
  const [loginOpen, setLoginOpen] = useState(false);
  const [workspaceEntryPath, setWorkspaceEntryPath] = useState<string | null>(
    null,
  );
  const sessionQuery = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
    retry: false,
  });
  const projectsQuery = useQuery({
    enabled: sessionQuery.isSuccess,
    queryFn: listProjects,
    queryKey: ["projects"],
    retry: false,
  });

  const canResolveSessionEntry =
    sessionQuery.isSuccess &&
    (hasProjectScopedReturnTo(returnTo) ||
      projectsQuery.isSuccess ||
      projectsQuery.isError);
  const sessionEntryPath = canResolveSessionEntry
    ? resolveLoginDestinationFromProjects(returnTo, projectsQuery.data ?? [])
    : null;
  const effectiveEntryPath = workspaceEntryPath ?? sessionEntryPath;
  const sessionChecking = sessionQuery.isPending;
  const hasWorkspaceEntry =
    sessionChecking || Boolean(workspaceEntryPath) || sessionQuery.isSuccess;
  const entryResolving = hasWorkspaceEntry && !effectiveEntryPath;

  function handleSuccess(path: string) {
    setWorkspaceEntryPath(path);
    setLoginOpen(false);
  }

  function openWorkspaceEntry() {
    if (entryResolving) {
      return;
    }
    if (effectiveEntryPath) {
      router.push(effectiveEntryPath);
      return;
    }
    setLoginOpen(true);
  }

  return (
    <main className="min-h-screen bg-[var(--canvas)] text-[var(--ink)]">
      <header className="sticky top-0 z-40 border-b border-[var(--hairline)] bg-[var(--canvas)] backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-5 sm:px-8">
          <div className="flex min-w-0 items-center gap-8">
            <div
              className="flex min-w-0 items-center gap-3"
              data-testid="landing-brand"
            >
              <BrandMark />
              <span className="font-display truncate text-sm font-semibold">
                Warmy Agent Test
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle className="size-9 text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]" />
            <button
              className="inline-flex h-9 items-center justify-center rounded-[var(--radius-pill)] bg-[var(--primary)] px-5 text-sm font-medium text-white transition-all hover:bg-[var(--primary-active)] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={entryResolving}
              onClick={openWorkspaceEntry}
              type="button"
            >
              {hasWorkspaceEntry ? "工作台" : "登录"}
            </button>
          </div>
        </div>
      </header>

      <section className="border-b border-[var(--hairline)] bg-[var(--canvas)]">
        <div className="mx-auto grid min-h-[calc(100vh-3.5rem)] max-w-7xl items-center gap-12 px-5 py-14 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:py-20">
          <div className="max-w-2xl">
            <p className="inline-flex items-center gap-2 rounded-[var(--radius-pill)] border border-[var(--hairline)] bg-[var(--surface)] px-3 py-1.5 text-xs text-[var(--body)]">
              <Sparkles
                aria-hidden="true"
                className="size-3.5 text-[var(--primary)]"
              />
              Agent 发布前的测试证据层
            </p>
            <h1 className="mt-6 text-[42px] font-semibold leading-[1.05] tracking-normal sm:text-[64px]">
              把 AI Agent 的每次变更，变成可发布的证据。
            </h1>
            <p className="mt-6 max-w-xl text-[17px] leading-7 text-[var(--body)]">
              从测试 Agent
              生成用例，到浏览器执行、评分、安全测试和人工审核，所有结果沉淀到同一条发布链路里。
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <button
                className="inline-flex h-11 items-center justify-center rounded-[var(--radius-pill)] bg-[var(--primary)] px-6 text-[15px] font-medium text-white transition-all hover:bg-[var(--primary-active)] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={entryResolving}
                onClick={openWorkspaceEntry}
                type="button"
              >
                进入工作台
              </button>
              <button
                className="inline-flex h-11 items-center gap-2 rounded-[var(--radius-pill)] border border-[var(--hairline-strong)] bg-[var(--surface)] px-5 text-[15px] text-[var(--ink)] transition-colors hover:bg-[var(--canvas-soft)] disabled:cursor-not-allowed disabled:opacity-60"
                disabled={entryResolving}
                onClick={openWorkspaceEntry}
                type="button"
              >
                查看闭环路径
                <ArrowRight aria-hidden="true" className="size-4" />
              </button>
            </div>
            <div className="mt-10 grid gap-3 sm:grid-cols-3">
              <ProofMetric label="生成测试资产" value="Agent" />
              <ProofMetric label="运行与证据" value="Trace" />
              <ProofMetric label="发布前把关" value="Gate" />
            </div>
          </div>

          <EvidenceMap />
        </div>
      </section>

      <section className="bg-[var(--canvas)] px-5 py-16 text-[var(--ink)] sm:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-2xl">
            <p className="text-sm font-medium text-[var(--primary)]">
              End-to-end workflow
            </p>
            <h2 className="mt-3 text-[34px] font-semibold leading-tight tracking-normal">
              从生成、执行到放行，减少用户理解成本。
            </h2>
          </div>
          <div className="mt-8 grid gap-4 lg:grid-cols-4">
            <WorkflowCard
              icon={<Bot aria-hidden="true" />}
              label="测试 Agent"
              text="对话生成用例，人工确认后同步到用例库。"
            />
            <WorkflowCard
              icon={<PlayCircle aria-hidden="true" />}
              label="运行中心"
              text="绑定版本后启动执行，进度、截图和 Trace 聚合展示。"
            />
            <WorkflowCard
              icon={<FlaskConical aria-hidden="true" />}
              label="评分与安全"
              text="评分器、安全策略和失败证据统一进入结果。"
            />
            <WorkflowCard
              icon={<ShieldCheck aria-hidden="true" />}
              label="发布门禁"
              text="人工审核通过后，形成可追溯的发布结论。"
            />
          </div>
        </div>
      </section>

      <footer className="border-t border-[var(--hairline)] bg-[var(--canvas-soft)] px-5 py-8 text-center text-xs text-[var(--muted)]">
        内部账号访问。管理员创建用户后即可进入测试 Agent 工作流。
      </footer>

      <Dialog onOpenChange={setLoginOpen} open={loginOpen}>
        <DialogContent className="w-[min(27rem,calc(100vw-2rem))] p-6">
          <DialogTitle className="text-[28px] font-semibold leading-tight tracking-normal">
            登录测试工作台
          </DialogTitle>
          <DialogDescription>
            使用组织账号继续，登录后进入测试 Agent 工作流。
          </DialogDescription>
          <div className="mt-6">
            <LoginForm onSuccess={handleSuccess} returnTo={returnTo} />
          </div>
          <div className="mt-5 flex items-center justify-center gap-2 text-xs text-[var(--muted)]">
            <CheckCircle2
              aria-hidden="true"
              className="size-3.5 text-[var(--success)]"
            />
            <span>会话受保护 · 凭证加密传输</span>
          </div>
        </DialogContent>
      </Dialog>
    </main>
  );
}

function EvidenceMap() {
  return (
    <div
      aria-label="测试发布闭环"
      className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--hairline)] pb-5">
        <div>
          <p className="text-sm font-semibold text-[var(--primary)]">
            Release readiness
          </p>
          <h2 className="mt-2 text-[28px] font-semibold leading-tight tracking-normal">
            发布前证据链
          </h2>
          <p className="mt-2 max-w-lg text-sm leading-6 text-[var(--muted)]">
            不展示桌面壳，只展示用户真正要理解的 Web
            平台链路：资产、执行、评估、审核和门禁。
          </p>
        </div>
        <span className="rounded-[var(--radius-pill)] bg-[var(--success-subtle)] px-3 py-1.5 text-xs font-medium text-[var(--success)]">
          发布风险低
        </span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {EVIDENCE_STEPS.map((step, index) => (
          <EvidenceStep key={step.label} order={index + 1} {...step} />
        ))}
      </div>

      <div className="mt-5 grid gap-3 border-t border-[var(--hairline)] pt-5 sm:grid-cols-3">
        <ReleaseStat label="已同步用例" value="128" />
        <ReleaseStat label="通过率" value="96%" />
        <ReleaseStat label="待人工确认" value="5" />
      </div>
    </div>
  );
}

function ProofMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3">
      <p className="text-sm font-semibold">{value}</p>
      <p className="mt-1 text-xs text-[var(--muted)]">{label}</p>
    </div>
  );
}

function EvidenceStep({
  icon,
  label,
  order,
  state,
  text,
}: {
  icon: ReactNode;
  label: string;
  order: number;
  state: string;
  text: string;
}) {
  return (
    <div className="min-h-32 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--canvas-soft)] p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="grid size-9 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)] [&_svg]:size-4">
          {icon}
        </span>
        <span className="rounded-[var(--radius-pill)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--muted)]">
          {state}
        </span>
      </div>
      <p className="mt-4 text-xs font-medium text-[var(--primary)]">0{order}</p>
      <h3 className="mt-1 text-[17px] font-semibold">{label}</h3>
      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{text}</p>
    </div>
  );
}

function ReleaseStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius-md)] bg-[var(--canvas-soft)] px-4 py-3">
      <p className="text-[26px] font-semibold leading-none">{value}</p>
      <p className="mt-2 text-xs text-[var(--muted)]">{label}</p>
    </div>
  );
}

function WorkflowCard({
  icon,
  label,
  text,
}: {
  icon: ReactNode;
  label: string;
  text: string;
}) {
  return (
    <article className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-5">
      <span className="grid size-10 place-items-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)] [&_svg]:size-4">
        {icon}
      </span>
      <h3 className="mt-5 text-[17px] font-semibold">{label}</h3>
      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{text}</p>
    </article>
  );
}
