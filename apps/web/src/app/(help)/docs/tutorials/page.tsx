import { ArrowLeft, Play, Video } from "lucide-react";
import Link from "next/link";

const tutorials = [
  {
    description: "了解如何创建和配置测试 Agent，包括连接参数设置和版本发布",
    duration: "5:30",
    thumbnail: "🎬",
    title: "Agent 创建与配置",
  },
  {
    description: "学习如何创建数据集、批量导入测试用例和管理版本",
    duration: "8:15",
    thumbnail: "📋",
    title: "数据集管理入门",
  },
  {
    description: "掌握测试计划的创建、配置和执行流程",
    duration: "6:45",
    thumbnail: "🚀",
    title: "测试计划执行",
  },
  {
    description: "了解如何查看测试报告、分析 Trace 和定位问题",
    duration: "10:20",
    thumbnail: "📊",
    title: "测试报告分析",
  },
  {
    description: "学习如何配置环境模板和管理测试凭证",
    duration: "4:50",
    thumbnail: "🔧",
    title: "环境配置指南",
  },
  {
    description: "了解如何使用安全测试功能检测敏感信息泄露",
    duration: "7:00",
    thumbnail: "🛡️",
    title: "安全测试入门",
  },
];

export default function TutorialsPage() {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-[900px] items-center justify-between px-6">
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

      <div className="mx-auto max-w-[900px] px-6 py-8">
        <header className="mb-8">
          <div className="flex items-center gap-3">
            <Video className="size-8 text-[var(--accent)]" />
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                视频教程
              </h1>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                通过视频快速学习平台的核心功能
              </p>
            </div>
          </div>
        </header>

        <div className="grid gap-4 sm:grid-cols-2">
          {tutorials.map((tutorial, i) => (
            <div
              className="group cursor-pointer rounded-xl border border-[var(--border)] bg-[var(--surface)] transition-all hover:border-[var(--accent)] hover:shadow-md"
              key={i}
            >
              <div className="flex h-32 items-center justify-center rounded-t-xl bg-[var(--surface-subtle)] text-4xl">
                {tutorial.thumbnail}
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold group-hover:text-[var(--accent)]">
                    {tutorial.title}
                  </h3>
                  <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                    <Play className="size-3" />
                    {tutorial.duration}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[var(--text-muted)]">
                  {tutorial.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
