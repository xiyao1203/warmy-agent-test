import {
  Bot,
  Database,
  FileChartColumn,
  KeyRound,
  ListChecks,
  ShieldCheck,
} from "lucide-react";

const tutorials = [
  {
    description: "配置连接参数、验证连通性，并发布一个不可变 Agent 版本。",
    duration: "约 6 分钟",
    icon: Bot,
    title: "Agent 创建与版本发布",
  },
  {
    description: "组织数据集、批量导入测试用例，并管理可复现的资产版本。",
    duration: "约 8 分钟",
    icon: Database,
    title: "数据集与测试用例",
  },
  {
    description: "组合 Agent、数据集、环境和评分器，形成可运行的测试计划。",
    duration: "约 7 分钟",
    icon: ListChecks,
    title: "测试计划配置",
  },
  {
    description: "阅读运行状态、Agent Trace、评分证据和失败分类。",
    duration: "约 10 分钟",
    icon: FileChartColumn,
    title: "结果与报告分析",
  },
  {
    description: "创建隔离的测试环境，安全管理变量与项目凭证。",
    duration: "约 5 分钟",
    icon: KeyRound,
    title: "环境与凭证",
  },
  {
    description: "配置安全规则，识别敏感信息泄露、越权和高风险工具调用。",
    duration: "约 7 分钟",
    icon: ShieldCheck,
    title: "安全测试入门",
  },
] as const;

export default function TutorialsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-3xl">
        <p className="text-sm font-medium text-[var(--muted)]">
          帮助中心 / 教程
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">产品教程</h1>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          按工作流程阅读平台核心能力，快速完成配置、执行和结果分析。
        </p>
      </header>

      <section aria-labelledby="tutorial-list-title">
        <h2 className="sr-only" id="tutorial-list-title">
          教程目录
        </h2>
        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          {tutorials.map(({ description, duration, icon: Icon, title }) => (
            <article
              className="flex items-start gap-4 border-b border-[var(--hairline)] px-4 py-4 last:border-b-0 sm:px-5"
              key={title}
            >
              <span className="flex size-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--muted)]">
                <Icon className="size-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <h3 className="text-sm font-semibold">{title}</h3>
                  <span className="text-xs text-[var(--body)]">{duration}</span>
                </div>
                <p className="mt-1 text-sm leading-5 text-[var(--muted)]">
                  {description}
                </p>
              </div>
              <span className="shrink-0 rounded-full bg-[var(--canvas-soft)] px-2 py-1 text-xs font-medium text-[var(--muted)]">
                阅读指南
              </span>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
