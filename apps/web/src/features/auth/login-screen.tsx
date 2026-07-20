"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  Bot,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Gauge,
  GitCompareArrows,
  ShieldCheck,
} from "lucide-react";
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
import { MetricCard, MetricGrid } from "@/components/ui/metric-card";
import { listProjects } from "@/features/projects";

import { getCurrentUser } from "./api";
import {
  hasProjectScopedReturnTo,
  resolveLoginDestinationFromProjects,
} from "./login-destination";
import { LoginForm } from "./login-form";

const RUN_ROWS = [
  {
    agent: "Customer Support Agent v2.8",
    progress: "68 / 100",
    run: "Run #1842",
    state: "运行中",
    tone: "info",
  },
  {
    agent: "Canvas Agent v4.1",
    progress: "98.2% 通过",
    run: "Run #1841",
    state: "已完成",
    tone: "success",
  },
  {
    agent: "Browser Agent v1.6",
    progress: "3 个执行错误",
    run: "Run #1840",
    state: "需处理",
    tone: "danger",
  },
] as const;

const CAPABILITIES = [
  {
    icon: <Bot aria-hidden="true" />,
    label: "测试资产",
    text: "对话生成的用例、计划和评分规则保持结构化、可编辑、可追溯。",
  },
  {
    icon: <Activity aria-hidden="true" />,
    label: "真实执行",
    text: "API 与浏览器运行持续采集 Trace、截图、产物、成本和状态变化。",
  },
  {
    icon: <ShieldCheck aria-hidden="true" />,
    label: "质量门禁",
    text: "自动评分、安全测试和人工审核共同形成可解释的发布结论。",
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
  const authenticated = Boolean(workspaceEntryPath) || sessionQuery.isSuccess;
  const entryResolving =
    sessionChecking || (authenticated && !effectiveEntryPath);
  const headerEntryLabel = authenticated ? "工作台" : "登录";
  const heroEntryLabel = authenticated ? "进入工作台" : "登录并开始";

  function handleSuccess(path: string) {
    setWorkspaceEntryPath(path);
    setLoginOpen(false);
  }

  function openWorkspaceEntry() {
    if (entryResolving) return;
    if (effectiveEntryPath) {
      router.push(effectiveEntryPath);
      return;
    }
    setLoginOpen(true);
  }

  return (
    <main className="min-h-screen bg-[var(--canvas)] text-[var(--ink)]">
      <header className="sticky top-0 z-40 border-b border-[var(--hairline)] bg-[var(--surface)]">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-5 sm:px-8">
          <div
            className="flex min-w-0 items-center gap-3"
            data-testid="landing-brand"
          >
            <BrandMark />
            <span className="font-display truncate text-sm font-semibold">
              Warmy Agent Test
            </span>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle className="size-9 text-[var(--muted)] hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]" />
            <button
              aria-busy={entryResolving}
              className="inline-flex h-9 min-w-20 items-center justify-center rounded-[var(--radius-md)] bg-[var(--primary)] px-4 text-sm font-semibold text-[var(--on-primary)] transition-[background,transform] duration-[var(--motion-fast)] hover:bg-[var(--primary-active)] active:translate-y-px disabled:cursor-not-allowed disabled:translate-y-0 disabled:opacity-60"
              disabled={entryResolving}
              onClick={openWorkspaceEntry}
              type="button"
            >
              {headerEntryLabel}
            </button>
          </div>
        </div>
      </header>

      <section className="border-b border-[var(--hairline)]">
        <div className="mx-auto flex min-h-[calc(92svh-3.5rem)] max-w-7xl flex-col justify-center px-5 pb-12 pt-14 sm:px-8 sm:pt-16">
          <div className="mx-auto max-w-4xl text-center">
            <p className="text-sm font-medium text-[var(--primary)]">
              Agent testing and release evidence
            </p>
            <h1 className="mt-4 text-[42px] font-semibold leading-[1.05] sm:text-[58px]">
              Warmy Agent Test
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-[var(--body)] sm:text-[17px]">
              持续验证 Agent
              的能力、质量与安全，把每次执行沉淀为可复现、可审核、可放行的测试证据。
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <button
                aria-busy={entryResolving}
                className="inline-flex h-10 items-center justify-center rounded-[var(--radius-md)] bg-[var(--primary)] px-5 text-sm font-semibold text-[var(--on-primary)] transition-[background,transform] duration-[var(--motion-fast)] hover:bg-[var(--primary-active)] active:translate-y-px disabled:cursor-not-allowed disabled:translate-y-0 disabled:opacity-60"
                disabled={entryResolving}
                onClick={openWorkspaceEntry}
                type="button"
              >
                {heroEntryLabel}
              </button>
              <a
                className="inline-flex h-10 items-center gap-2 rounded-[var(--radius-md)] border border-[var(--hairline-strong)] bg-[var(--surface)] px-4 text-sm font-semibold text-[var(--ink)] transition-[background,border-color,transform] duration-[var(--motion-fast)] hover:bg-[var(--canvas-soft)] active:translate-y-px"
                href="#product-evidence"
              >
                查看运行证据
                <ArrowRight aria-hidden="true" className="size-4" />
              </a>
            </div>
          </div>

          <div className="mt-12 sm:mt-14">
            <ProductEvidence />
          </div>
        </div>
      </section>

      <section className="border-b border-[var(--hairline)] bg-[var(--surface)]">
        <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
          <div className="max-w-2xl">
            <p className="text-sm font-medium text-[var(--primary)]">
              一条连续的质量链路
            </p>
            <h2 className="mt-3 text-[30px] font-semibold leading-tight">
              从测试资产到发布结论，每一步都有证据。
            </h2>
          </div>
          <div className="mt-9 grid border-y border-[var(--hairline)] md:grid-cols-3">
            {CAPABILITIES.map((capability) => (
              <Capability key={capability.label} {...capability} />
            ))}
          </div>
        </div>
      </section>

      <section className="bg-[var(--canvas-soft)]">
        <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
          <div className="grid gap-8 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
            <div>
              <p className="text-sm font-medium text-[var(--primary)]">
                Release confidence
              </p>
              <h2 className="mt-3 text-[30px] font-semibold leading-tight">
                看清退化、风险与阻塞，再决定是否发布。
              </h2>
              <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
                运行结果关联具体版本、用例、Trace、评分和审核意见，失败可以直接进入回归闭环。
              </p>
            </div>
            <div className="border-l border-[var(--hairline)] lg:pl-8">
              <EvidenceLine
                icon={<GitCompareArrows aria-hidden="true" />}
                label="版本对比"
                text="3 个关键用例出现退化，已定位到工具调用顺序。"
              />
              <EvidenceLine
                icon={<Gauge aria-hidden="true" />}
                label="评分与安全"
                text="质量评分 0.92，安全检查无高危发现。"
              />
              <EvidenceLine
                icon={<ShieldCheck aria-hidden="true" />}
                label="发布门禁"
                text="关键阈值已满足，等待 1 项人工审核结论。"
              />
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-[var(--hairline)] bg-[var(--surface)] px-5 py-8 text-center text-xs text-[var(--muted)]">
        使用组织账号登录。账号与项目权限由超级管理员统一管理。
      </footer>

      <Dialog onOpenChange={setLoginOpen} open={loginOpen}>
        <DialogContent className="w-[min(27rem,calc(100vw-2rem))] p-6">
          <DialogTitle className="text-[28px] font-semibold leading-tight">
            登录测试工作台
          </DialogTitle>
          <DialogDescription>
            使用组织账号继续，登录后可选择进入已授权的项目工作台。
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

function ProductEvidence() {
  return (
    <section
      aria-label="真实运行证据"
      className="overflow-hidden border-y border-[var(--hairline)] bg-[var(--surface)] shadow-[var(--shadow-product)]"
      id="product-evidence"
    >
      <div className="flex min-h-11 items-center justify-between gap-4 border-b border-[var(--hairline)] px-4">
        <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
          <span>测试执行</span>
          <span>/</span>
          <strong className="text-[var(--ink)]">运行中心</strong>
        </div>
        <span className="inline-flex items-center gap-1.5 text-xs text-[var(--success)]">
          <span className="size-1.5 rounded-full bg-[var(--success)]" />
          数据已更新
        </span>
      </div>

      <div className="p-4 sm:p-5">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">发布候选 v4.1 回归</h2>
            <p className="mt-1 text-xs text-[var(--muted)]">
              100 条用例 · API 与浏览器混合执行 · 基线 v4.0
            </p>
          </div>
          <span className="hidden text-xs text-[var(--muted)] sm:inline">
            刚刚同步
          </span>
        </div>

        <MetricGrid className="mt-4">
          <MetricCard
            change="+42"
            icon={<Activity aria-hidden="true" />}
            label="全部运行"
            state="updated"
            tone="accent"
            value="1,284"
          />
          <MetricCard
            change="实时"
            icon={<Clock3 aria-hidden="true" />}
            label="运行中"
            state="running"
            tone="info"
            value="12"
          />
          <MetricCard
            change="+1.8%"
            icon={<CheckCircle2 aria-hidden="true" />}
            label="通过率"
            state="updated"
            tone="success"
            value="96.4%"
          />
          <MetricCard
            change="3 新增"
            icon={<CircleAlert aria-hidden="true" />}
            label="异常运行"
            state="warning"
            tone="danger"
            value="8"
          />
        </MetricGrid>

        <div className="mt-4 grid border-t border-[var(--hairline)] lg:grid-cols-[1.3fr_0.7fr]">
          <div className="min-w-0 pt-3 lg:pr-5">
            <div className="grid grid-cols-[0.65fr_1fr_0.55fr_0.55fr] gap-3 border-b border-[var(--hairline)] px-2 pb-2 text-xs text-[var(--muted)] max-sm:grid-cols-[0.75fr_1fr_0.65fr]">
              <span>运行</span>
              <span>Agent</span>
              <span>状态</span>
              <span className="max-sm:hidden">结果</span>
            </div>
            {RUN_ROWS.map((run) => (
              <RunRow key={run.run} {...run} />
            ))}
          </div>

          <aside className="border-t border-[var(--hairline)] pt-4 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-3">
            <p className="text-xs font-semibold text-[var(--ink)]">当前证据</p>
            <EvidenceCheck label="Trace 完整" value="100%" />
            <EvidenceCheck label="安全发现" value="0 高危" />
            <EvidenceCheck label="人工审核" value="1 待处理" />
            <EvidenceCheck label="发布门禁" value="条件通过" />
          </aside>
        </div>
      </div>
    </section>
  );
}

function RunRow({
  agent,
  progress,
  run,
  state,
  tone,
}: (typeof RUN_ROWS)[number]) {
  return (
    <div className="grid min-h-11 grid-cols-[0.65fr_1fr_0.55fr_0.55fr] items-center gap-3 border-b border-[var(--hairline-soft)] px-2 text-xs last:border-b-0 max-sm:grid-cols-[0.75fr_1fr_0.65fr]">
      <strong className="font-medium">{run}</strong>
      <span className="truncate text-[var(--muted)]">{agent}</span>
      <span className="inline-flex items-center gap-1.5">
        <span
          className={`size-1.5 rounded-full ${
            tone === "success"
              ? "bg-[var(--success)]"
              : tone === "danger"
                ? "bg-[var(--danger)]"
                : "bg-[var(--info)]"
          }`}
        />
        {state}
      </span>
      <span className="text-[var(--muted)] max-sm:hidden">{progress}</span>
    </div>
  );
}

function EvidenceCheck({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[var(--hairline-soft)] py-2.5 text-xs last:border-b-0">
      <span className="text-[var(--muted)]">{label}</span>
      <strong className="font-medium">{value}</strong>
    </div>
  );
}

function Capability({
  icon,
  label,
  text,
}: {
  icon: ReactNode;
  label: string;
  text: string;
}) {
  return (
    <article className="border-b border-[var(--hairline)] py-6 md:border-b-0 md:border-r md:px-6 md:first:pl-0 md:last:border-r-0 md:last:pr-0">
      <span className="grid size-6 place-items-center text-[var(--primary)] [&_svg]:size-[var(--icon-optical-size)]">
        {icon}
      </span>
      <h3 className="mt-4 text-base font-semibold">{label}</h3>
      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{text}</p>
    </article>
  );
}

function EvidenceLine({
  icon,
  label,
  text,
}: {
  icon: ReactNode;
  label: string;
  text: string;
}) {
  return (
    <div className="flex gap-4 border-b border-[var(--hairline)] py-4 first:pt-0 last:border-b-0 last:pb-0">
      <span className="grid size-7 shrink-0 place-items-center text-[var(--primary)] [&_svg]:size-[var(--icon-optical-size)]">
        {icon}
      </span>
      <div>
        <h3 className="text-sm font-semibold">{label}</h3>
        <p className="mt-1 text-sm leading-6 text-[var(--muted)]">{text}</p>
      </div>
    </div>
  );
}
