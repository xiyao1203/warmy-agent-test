import { AppShell } from "@/components/layout/app-shell";

export default function HomePage() {
  return (
    <AppShell projectName="Demo Project" userName="Jason">
      <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6">
        <p className="text-sm text-[var(--text-muted)]">平台基础</p>
        <h1 className="mt-2 text-2xl font-semibold">Agent 测试工作台</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--text-muted)]">
          工程基线正在建立中。后续将在这里管理
          Agent、数据集、测试计划与运行结果。
        </p>
      </section>
    </AppShell>
  );
}
