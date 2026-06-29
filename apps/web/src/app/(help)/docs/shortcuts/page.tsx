import { ArrowLeft, Keyboard } from "lucide-react";
import Link from "next/link";

const shortcutGroups = [
  {
    shortcuts: [
      { description: "打开全局搜索", keys: ["⌘", "K"] },
      { description: "打开帮助文档", keys: ["⌘", "/"] },
      { description: "切换项目", keys: ["⌘", "P"] },
    ],
    title: "全局",
  },
  {
    shortcuts: [
      { description: "保存当前更改", keys: ["⌘", "S"] },
      { description: "取消编辑", keys: ["Escape"] },
      { description: "提交表单", keys: ["⌘", "Enter"] },
    ],
    title: "编辑",
  },
  {
    shortcuts: [
      { description: "创建新项目", keys: ["⌘", "N"] },
      { description: "刷新数据", keys: ["⌘", "R"] },
      { description: "返回列表", keys: ["⌘", "←"] },
    ],
    title: "导航",
  },
  {
    shortcuts: [
      { description: "选择上一项", keys: ["↑"] },
      { description: "选择下一项", keys: ["↓"] },
      { description: "确认选择", keys: ["Enter"] },
    ],
    title: "列表操作",
  },
];

export default function ShortcutsPage() {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-[700px] items-center justify-between px-6">
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

      <div className="mx-auto max-w-[700px] px-6 py-8">
        <header className="mb-8">
          <div className="flex items-center gap-3">
            <Keyboard className="size-8 text-[var(--accent)]" />
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                键盘快捷键
              </h1>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                使用键盘快捷键提升操作效率
              </p>
            </div>
          </div>
        </header>

        <div className="space-y-8">
          {shortcutGroups.map((group) => (
            <section key={group.title}>
              <h2 className="mb-4 text-lg font-semibold">{group.title}</h2>
              <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)]">
                {group.shortcuts.map((shortcut, i) => (
                  <div
                    className={`flex items-center justify-between px-5 py-3.5 ${
                      i !== group.shortcuts.length - 1
                        ? "border-b border-[var(--border)]"
                        : ""
                    }`}
                    key={i}
                  >
                    <span className="text-sm">{shortcut.description}</span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, j) => (
                        <kbd
                          className="rounded-md border border-[var(--border)] bg-[var(--surface-subtle)] px-2 py-1 text-xs font-medium shadow-sm"
                          key={j}
                        >
                          {key}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>

        <div className="mt-8 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <h3 className="font-semibold">提示</h3>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            在 macOS 上使用{" "}
            <kbd className="rounded border border-[var(--border)] bg-[var(--surface-subtle)] px-1.5 py-0.5 text-xs">
              ⌘
            </kbd>{" "}
            键，在 Windows/Linux 上使用{" "}
            <kbd className="rounded border border-[var(--border)] bg-[var(--surface-subtle)] px-1.5 py-0.5 text-xs">
              Ctrl
            </kbd>{" "}
            键。
          </p>
        </div>
      </div>
    </div>
  );
}
