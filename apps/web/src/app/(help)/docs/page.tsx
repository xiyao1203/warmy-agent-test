import {
  ArrowRight,
  BookOpen,
  ChevronDown,
  FileText,
  GraduationCap,
  Keyboard,
  MessageSquare,
  Rocket,
} from "lucide-react";
import Link from "next/link";

import { HelpSearch, type HelpTopic } from "@/features/help";

const helpTopics: HelpTopic[] = [
  {
    id: "quickstart",
    title: "快速开始",
    description: "从创建项目到完成第一次测试运行",
    href: "/docs#quickstart",
    category: "入门",
  },
  {
    id: "test-cases",
    title: "测试用例指南",
    description: "编写清晰、可重复执行的 Agent 测试用例",
    href: "/docs/test-cases",
    category: "测试资产",
  },
  {
    id: "tutorials",
    title: "产品教程",
    description: "按主题了解 Agent、数据集、测试计划和报告",
    href: "/docs/tutorials",
    category: "教程",
  },
  {
    id: "shortcuts",
    title: "键盘快捷键",
    description: "使用键盘完成常用导航和编辑操作",
    href: "/docs/shortcuts",
    category: "效率",
  },
  {
    id: "feedback",
    title: "反馈与建议",
    description: "报告问题或告诉我们你希望改进的地方",
    href: "/feedback",
    category: "支持",
  },
];

const topicCards = [
  {
    description: "从测试目标拆解到可验证的输入、步骤和预期结果。",
    href: "/docs/test-cases",
    icon: FileText,
    label: "编写测试用例",
  },
  {
    description: "按模块阅读核心能力说明，建立完整的平台操作路径。",
    href: "/docs/tutorials",
    icon: GraduationCap,
    label: "浏览产品教程",
  },
  {
    description: "查看平台支持的导航、编辑和列表操作快捷键。",
    href: "/docs/shortcuts",
    icon: Keyboard,
    label: "掌握快捷键",
  },
  {
    description: "提交问题、体验建议或新的功能需求。",
    href: "/feedback",
    icon: MessageSquare,
    label: "联系产品团队",
  },
];

const quickstartSteps = [
  ["创建项目", "定义测试资产、成员和环境的隔离边界。"],
  ["接入 Agent", "填写连接信息并发布一个不可变版本。"],
  ["准备测试用例", "创建数据集，录入输入、断言和预期结果。"],
  ["配置测试计划", "选择 Agent、数据集、环境和评分器。"],
  ["运行并分析", "查看运行状态、Trace、评分和失败证据。"],
] as const;

const faqs = [
  [
    "如何批量导入测试用例？",
    "在数据集详情中使用导入功能，按页面提供的模板准备结构化用例数据。导入前先校验必填字段和用例唯一标识。",
  ],
  [
    "Agent 版本发布后还能修改吗？",
    "不能。已发布版本保持不可变，以确保历史运行可重现。需要调整时请创建并发布新版本。",
  ],
  [
    "测试环境和凭证如何管理？",
    "在环境与凭证页面创建环境模板。普通成员可以在授权范围内执行任务，但不能读取凭证明文。",
  ],
  [
    "在哪里定位失败原因？",
    "从运行详情进入结果工作台，结合用例输入输出、Agent Trace、评分证据和产物定位失败步骤。",
  ],
] as const;

export default function DocsPage() {
  return (
    <div className="space-y-12">
      <header className="max-w-3xl">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-[var(--muted)]">
          <BookOpen className="size-4" />
          文档与指南
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">帮助中心</h1>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          查找平台使用说明、测试实践和常见问题，快速完成从 Agent
          接入到结果分析的完整流程。
        </p>
      </header>

      <section aria-labelledby="help-search-title" className="space-y-4">
        <div>
          <h2 className="text-base font-semibold" id="help-search-title">
            从哪里开始？
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            搜索主题、功能或操作名称。
          </p>
        </div>
        <HelpSearch topics={helpTopics} />
      </section>

      <section aria-labelledby="topics-title">
        <div className="mb-4">
          <h2 className="text-base font-semibold" id="topics-title">
            浏览主题
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            选择最接近当前任务的指南。
          </p>
        </div>
        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          {topicCards.map(({ description, href, icon: Icon, label }, index) => (
            <Link
              className="group flex items-start gap-3 px-4 py-4 transition-colors hover:bg-[var(--canvas-soft)]"
              href={href}
              key={href}
            >
              <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--muted)]">
                <Icon className="size-4" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="text-sm font-medium">{label}</span>
                <span className="mt-1 block text-sm leading-5 text-[var(--muted)]">
                  {description}
                </span>
              </span>
              <ArrowRight className="mt-1 size-4 shrink-0 text-[var(--body)] transition-transform group-hover:translate-x-0.5 group-hover:text-[var(--ink)]" />
              {index < topicCards.length - 1 && (
                <span className="sr-only">下一主题</span>
              )}
            </Link>
          ))}
        </div>
      </section>

      <section aria-labelledby="quickstart-title" id="quickstart">
        <div className="mb-4 flex items-start gap-3">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--primary-subtle)] text-[var(--primary)]">
            <Rocket className="size-4" />
          </span>
          <div>
            <h2 className="text-base font-semibold" id="quickstart-title">
              推荐上手路径
            </h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              按顺序完成以下步骤，建立第一条可复现的测试链路。
            </p>
          </div>
        </div>
        <ol className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          {quickstartSteps.map(([title, description], index) => (
            <li
              className="flex gap-4 border-b border-[var(--hairline)] px-4 py-4 last:border-b-0"
              key={title}
            >
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full border border-[var(--hairline-strong)] text-xs font-semibold text-[var(--muted)]">
                {index + 1}
              </span>
              <div>
                <h3 className="text-sm font-medium">{title}</h3>
                <p className="mt-1 text-sm leading-5 text-[var(--muted)]">
                  {description}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="faq-title" id="faq">
        <div className="mb-4">
          <h2 className="text-base font-semibold" id="faq-title">
            常见问题
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            开始配置和运行测试时最常遇到的问题。
          </p>
        </div>
        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          {faqs.map(([question, answer]) => (
            <details
              className="group border-b border-[var(--hairline)] last:border-b-0"
              key={question}
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-4 text-sm font-medium hover:bg-[var(--canvas-soft)]">
                {question}
                <ChevronDown className="size-4 shrink-0 text-[var(--muted)] transition-transform group-open:rotate-180" />
              </summary>
              <p className="border-t border-[var(--hairline)] px-4 py-4 text-sm leading-6 text-[var(--muted)]">
                {answer}
              </p>
            </details>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--canvas-soft)] p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold">没有找到需要的内容？</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            提交问题或建议，我们会把高频问题补充到帮助中心。
          </p>
        </div>
        <Link
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--on-primary)] hover:bg-[var(--primary-active)]"
          href="/feedback"
        >
          <MessageSquare className="size-4" />
          提交反馈
        </Link>
      </section>
    </div>
  );
}
