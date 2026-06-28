import {
  BookOpen,
  FileText,
  FlaskConical,
  PlayCircle,
  Settings,
  Shield,
} from "lucide-react";

const sections = [
  {
    description: "创建和管理测试 Agent，配置连接和发布版本",
    href: "/projects",
    icon: <FlaskConical className="size-5" />,
    title: "Agent 管理",
  },
  {
    description: "创建数据集、导入测试用例、管理版本",
    href: "/projects",
    icon: <FileText className="size-5" />,
    title: "数据集与用例",
  },
  {
    description: "组合 Agent、数据集和环境，配置执行门禁",
    href: "/projects",
    icon: <PlayCircle className="size-5" />,
    title: "测试计划",
  },
  {
    description: "管理测试环境模板、凭证和 Mock 服务",
    href: "/projects",
    icon: <Settings className="size-5" />,
    title: "环境与凭证",
  },
  {
    description: "配置安全扫描规则和漏洞检测",
    href: "/projects",
    icon: <Shield className="size-5" />,
    title: "安全测试",
  },
];

export default function DocsPage() {
  return (
    <div className="mx-auto max-w-[900px] px-6 py-8">
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <BookOpen className="size-8 text-[var(--accent)]" />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">帮助文档</h1>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              欢迎使用 Agent Test 平台，以下是各功能模块的使用指南。
            </p>
          </div>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        {sections.map((section) => (
          <a
            className="flex items-start gap-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 transition-colors hover:border-[var(--accent)] hover:bg-[var(--accent-subtle)]"
            href={section.href}
            key={section.title}
          >
            <div className="mt-0.5 text-[var(--text-muted)]">{section.icon}</div>
            <div>
              <h2 className="font-medium">{section.title}</h2>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                {section.description}
              </p>
            </div>
          </a>
        ))}
      </div>

      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold">快速开始</h2>
        <div className="space-y-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6">
          <div className="flex items-start gap-3">
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-xs font-semibold text-white">
              1
            </span>
            <div>
              <h3 className="font-medium">创建项目</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                在顶部项目选择器中创建或选择一个项目。
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-xs font-semibold text-white">
              2
            </span>
            <div>
              <h3 className="font-medium">配置 Agent</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                进入「智能体」页面，创建并配置测试 Agent。
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-xs font-semibold text-white">
              3
            </span>
            <div>
              <h3 className="font-medium">创建数据集</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                进入「测试用例」页面，创建数据集并添加测试用例。
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-xs font-semibold text-white">
              4
            </span>
            <div>
              <h3 className="font-medium">运行测试</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                进入「测试计划」页面，创建计划并启动测试执行。
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
