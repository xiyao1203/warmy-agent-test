import {
  ArrowLeft,
  BookOpen,
  FileText,
  FlaskConical,
  MessageSquare,
  PlayCircle,
  Search,
  Shield,
  Zap,
} from "lucide-react";
import Link from "next/link";

const features = [
  {
    description: "创建和管理测试 Agent，配置连接参数，发布不可变版本",
    gradient: "from-blue-500 to-cyan-500",
    href: "#agents",
    icon: <FlaskConical className="size-5" />,
    title: "Agent 管理",
  },
  {
    description: "创建数据集，批量导入测试用例，管理版本和标签",
    gradient: "from-purple-500 to-pink-500",
    href: "#datasets",
    icon: <FileText className="size-5" />,
    title: "数据集与用例",
  },
  {
    description: "组合 Agent、数据集和环境，配置执行策略和门禁规则",
    gradient: "from-orange-500 to-red-500",
    href: "#test-plans",
    icon: <PlayCircle className="size-5" />,
    title: "测试计划",
  },
  {
    description: "配置安全扫描规则，检测敏感信息泄露和权限问题",
    gradient: "from-green-500 to-emerald-500",
    href: "#security",
    icon: <Shield className="size-5" />,
    title: "安全测试",
  },
];

const quickLinks = [
  { description: "如何创建第一个 Agent？", href: "#quickstart" },
  { description: "如何导入测试用例？", href: "#import" },
  { description: "如何配置测试环境？", href: "#environment" },
  { description: "如何查看测试报告？", href: "#reports" },
];

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-[1100px] items-center justify-between px-6">
          <Link
            className="flex items-center gap-2 text-sm font-semibold transition-colors hover:text-[var(--accent)]"
            href="/projects"
          >
            <ArrowLeft className="size-4" />
            返回应用
          </Link>
          <span className="text-sm font-semibold">帮助中心</span>
          <div className="w-20" />
        </div>
      </header>

      {/* Hero Section */}
      <div className="border-b border-[var(--border)] bg-gradient-to-b from-[var(--accent-subtle)] to-transparent">
        <div className="mx-auto max-w-[1100px] px-6 py-12">
          <div className="flex items-start justify-between gap-8">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">帮助文档</h1>
              <p className="mt-3 text-lg text-[var(--text-muted)]">
                欢迎使用 Agent Test
                平台，这里可以帮助您快速上手并深入了解产品功能。
              </p>
              <div className="mt-6 flex gap-3">
                <a
                  className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--accent-strong)]"
                  href="#quickstart"
                >
                  <Zap className="size-4" />
                  快速开始
                </a>
                <a
                  className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm font-medium transition-colors hover:bg-[var(--surface-subtle)]"
                  href="#features"
                >
                  <BookOpen className="size-4" />
                  功能介绍
                </a>
              </div>
            </div>
            <div className="hidden w-80 shrink-0 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-lg lg:block">
              <div className="flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] px-3 py-2">
                <Search className="size-4 text-[var(--text-muted)]" />
                <span className="text-sm text-[var(--text-muted)]">
                  搜索文档...
                </span>
              </div>
              <div className="mt-4 space-y-2">
                {quickLinks.map((link, i) => (
                  <a
                    className="block rounded-md px-3 py-2 text-sm transition-colors hover:bg-[var(--surface-subtle)]"
                    href={link.href}
                    key={i}
                  >
                    <p className="text-[var(--text-muted)]">
                      {link.description}
                    </p>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1100px] px-6 py-10">
        {/* Features Section */}
        <section id="features">
          <h2 className="mb-2 text-xl font-semibold">功能模块</h2>
          <p className="mb-6 text-sm text-[var(--text-muted)]">
            了解平台各功能模块的使用方法
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {features.map((feature) => (
              <a
                className="group flex items-start gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-all hover:border-[var(--accent)] hover:shadow-md"
                href={feature.href}
                key={feature.title}
              >
                <div
                  className={`flex size-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br ${feature.gradient} text-white`}
                >
                  {feature.icon}
                </div>
                <div>
                  <h3 className="font-semibold group-hover:text-[var(--accent)]">
                    {feature.title}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">
                    {feature.description}
                  </p>
                </div>
              </a>
            ))}
          </div>
        </section>

        {/* Quick Start Section */}
        <section className="mt-12" id="quickstart">
          <h2 className="mb-2 text-xl font-semibold">快速开始</h2>
          <p className="mb-6 text-sm text-[var(--text-muted)]">
            按照以下步骤，快速体验平台核心功能
          </p>
          <div className="space-y-6">
            {[
              {
                content:
                  "在顶部导航栏的项目选择器中，点击「创建项目」按钮，输入项目名称和描述即可创建新项目。",
                step: 1,
                title: "创建项目",
              },
              {
                content:
                  "进入左侧导航「智能体」页面，点击「创建 Agent」按钮。填写 Agent 名称、类型和连接配置。",
                step: 2,
                title: "配置 Agent",
              },
              {
                content:
                  "进入「测试用例」页面，创建数据集后可通过 Excel 或 JSON 格式批量导入测试用例。",
                step: 3,
                title: "导入测试用例",
              },
              {
                content:
                  "进入「测试计划」页面，选择已发布的 Agent 和数据集版本，配置执行参数后即可启动测试。",
                step: 4,
                title: "创建并运行测试",
              },
              {
                content:
                  "在「测试执行」页面查看运行状态，点击运行 ID 进入详情页查看 Trace、截图和评分结果。",
                step: 5,
                title: "查看测试报告",
              },
            ].map((item) => (
              <div
                className="flex gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
                key={item.step}
              >
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-sm font-bold text-white">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">
                    {item.content}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* FAQ Section */}
        <section className="mt-12" id="faq">
          <h2 className="mb-2 text-xl font-semibold">常见问题</h2>
          <p className="mb-6 text-sm text-[var(--text-muted)]">
            快速找到常见问题的解答
          </p>
          <div className="space-y-3">
            {[
              {
                answer:
                  "在测试用例页面，选择数据集后点击「导入」按钮，支持 Excel (.xlsx) 和 JSON 两种格式。请参考测试指南了解模板格式。",
                question: "如何批量导入测试用例？",
              },
              {
                answer:
                  "Agent 版本一旦发布即为不可变状态，无法直接修改。如需更新，请创建新版本并发布。",
                question: "Agent 版本可以修改吗？",
              },
              {
                answer:
                  "在环境与凭证页面，可以创建环境模板并配置变量。测试计划执行时会自动注入对应环境的变量。",
                question: "如何配置测试环境变量？",
              },
              {
                answer:
                  "测试报告支持导出为 HTML 和 PDF 格式。在运行详情页，点击右上角「导出报告」按钮即可。",
                question: "如何导出测试报告？",
              },
            ].map((item, i) => (
              <details
                className="group rounded-xl border border-[var(--border)] bg-[var(--surface)]"
                key={i}
              >
                <summary className="flex cursor-pointer items-center justify-between px-5 py-4 text-sm font-medium transition-colors hover:bg-[var(--surface-subtle)] group-open:rounded-b-none">
                  {item.question}
                  <span className="text-[var(--text-muted)] transition-transform group-open:rotate-180">
                    ▼
                  </span>
                </summary>
                <div className="border-t border-[var(--border)] px-5 py-4 text-sm text-[var(--text-muted)]">
                  {item.answer}
                </div>
              </details>
            ))}
          </div>
        </section>

        {/* Contact Section */}
        <section className="mt-12 rounded-xl border border-[var(--accent)] bg-[var(--accent-subtle)] p-8 text-center">
          <MessageSquare className="mx-auto size-10 text-[var(--accent)]" />
          <h2 className="mt-4 text-xl font-semibold">还需要帮助？</h2>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            如果您没有找到想要的答案，欢迎提交反馈或联系技术支持
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--accent-strong)]"
              href="/feedback"
            >
              提交反馈
            </Link>
            <a
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm font-medium transition-colors hover:bg-[var(--surface-subtle)]"
              href="mailto:support@example.com"
            >
              联系支持
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
