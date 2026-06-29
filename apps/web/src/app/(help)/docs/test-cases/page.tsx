import { CheckCircle2, FileText, Lightbulb } from "lucide-react";

const structureSteps = [
  {
    description: "说明这条用例要验证的能力、风险或业务结果，避免一条用例覆盖多个互不相关的目标。",
    title: "先定义测试目标",
  },
  {
    description: "列出执行前必须存在的版本、环境、数据与权限条件，确保用例能够独立重放。",
    title: "写清前置条件",
  },
  {
    description: "提供 Agent 输入、工具约束和必要上下文，不用“正常处理”等模糊表达代替可验证要求。",
    title: "组织输入与步骤",
  },
  {
    description: "同时描述最终输出、关键工具调用、业务状态和安全边界，便于配置确定性断言与评分器。",
    title: "定义预期结果",
  },
] as const;

const bestPractices = [
  "一条用例只验证一个主要能力或风险点。",
  "边界条件、异常输入和权限不足场景单独成例。",
  "使用可观察的结果替代“合理”“正确”等主观描述。",
  "不要依赖其他用例的执行顺序或残留状态。",
  "修复后的高价值失败样本应加入固定回归集。",
] as const;

export default function TestCasesGuidePage() {
  return (
    <article className="space-y-10">
      <header className="max-w-3xl">
        <p className="text-sm font-medium text-[var(--text-muted)]">
          帮助中心 / 测试资产
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          测试用例编写指南
        </h1>
        <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
          把 Agent 的输入、过程、状态变化和最终输出拆成可以稳定执行与复核的结构化用例。
        </p>
      </header>

      <section aria-labelledby="case-structure-title">
        <div className="mb-4 flex items-center gap-2">
          <FileText className="size-4 text-[var(--text-muted)]" />
          <h2 className="text-base font-semibold" id="case-structure-title">
            用例结构
          </h2>
        </div>
        <ol className="border-l border-[var(--border)] pl-6">
          {structureSteps.map(({ description, title }, index) => (
            <li className="relative pb-7 last:pb-0" key={title}>
              <span className="absolute -left-[2.15rem] flex size-5 items-center justify-center rounded-full border border-[var(--border-strong)] bg-[var(--background)] text-[10px] font-semibold text-[var(--text-muted)]">
                {index + 1}
              </span>
              <h3 className="text-sm font-semibold">{title}</h3>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-[var(--text-muted)]">
                {description}
              </p>
            </li>
          ))}
        </ol>
      </section>

      <section
        aria-labelledby="best-practices-title"
        className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]"
      >
        <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-3">
          <Lightbulb className="size-4 text-[var(--text-muted)]" />
          <h2 className="text-sm font-semibold" id="best-practices-title">
            编写检查清单
          </h2>
        </div>
        <ul className="divide-y divide-[var(--border)]">
          {bestPractices.map((practice) => (
            <li className="flex items-start gap-3 px-4 py-3 text-sm" key={practice}>
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-[var(--success)]" />
              {practice}
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}
