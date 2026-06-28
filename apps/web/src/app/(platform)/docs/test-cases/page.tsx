import { ArrowLeft, FileText, Lightbulb, ListChecks } from "lucide-react";
import Link from "next/link";

export default function TestCasesGuidePage() {
  return (
    <div className="mx-auto max-w-[900px] px-6 py-8">
      <Link
        className="mb-6 inline-flex items-center gap-2 text-sm text-[var(--text-muted)] transition-colors hover:text-[var(--text)]"
        href="/docs"
      >
        <ArrowLeft className="size-4" />
        返回帮助文档
      </Link>

      <header className="mb-8">
        <div className="flex items-center gap-3">
          <FileText className="size-8 text-[var(--accent)]" />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">测试用例编写指南</h1>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              学习如何编写高质量的测试用例
            </p>
          </div>
        </div>
      </header>

      <div className="space-y-8">
        <section>
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <ListChecks className="size-5 text-[var(--accent)]" />
            测试用例结构
          </h2>
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6">
            <div className="space-y-4">
              <div>
                <h3 className="font-medium">用例名称</h3>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  简洁描述测试目标，例如「验证用户登录成功」
                </p>
              </div>
              <div>
                <h3 className="font-medium">前置条件</h3>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  执行测试前需要满足的条件，例如「用户已注册」
                </p>
              </div>
              <div>
                <h3 className="font-medium">测试步骤</h3>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  详细的操作步骤，每一步都要清晰明确
                </p>
              </div>
              <div>
                <h3 className="font-medium">预期结果</h3>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  每个步骤或整体的预期输出和行为
                </p>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Lightbulb className="size-5 text-[var(--accent)]" />
            最佳实践
          </h2>
          <div className="space-y-3">
            {[
              "每个用例只测试一个功能点",
              "使用清晰、简洁的语言描述步骤",
              "避免模糊的描述词，如「正常」「正确」",
              "包含边界条件和异常场景",
              "确保用例可独立执行，不依赖其他用例的执行顺序",
            ].map((tip, i) => (
              <div
                className="flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4"
                key={i}
              >
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--success)] text-xs font-semibold text-white">
                  ✓
                </span>
                <p className="text-sm">{tip}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
