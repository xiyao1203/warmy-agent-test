import { Keyboard } from "lucide-react";

const shortcutGroups = [
  {
    shortcuts: [
      { description: "打开全局搜索", keys: ["⌘", "K"] },
      { description: "打开帮助文档", keys: ["⌘", "/"] },
      { description: "切换项目", keys: ["⌘", "P"] },
    ],
    title: "全局导航",
  },
  {
    shortcuts: [
      { description: "保存当前更改", keys: ["⌘", "S"] },
      { description: "取消编辑或关闭弹层", keys: ["Esc"] },
      { description: "提交当前表单", keys: ["⌘", "Enter"] },
    ],
    title: "编辑操作",
  },
  {
    shortcuts: [
      { description: "选择上一项", keys: ["↑"] },
      { description: "选择下一项", keys: ["↓"] },
      { description: "确认选择", keys: ["Enter"] },
    ],
    title: "列表操作",
  },
] as const;

export default function ShortcutsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-3xl">
        <p className="text-sm font-medium text-[var(--text-muted)]">
          帮助中心 / 效率
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          键盘快捷键
        </h1>
        <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
          使用键盘完成常用导航和编辑操作。Windows 与 Linux 用户可将 ⌘ 替换为
          Ctrl。
        </p>
      </header>

      <div className="space-y-6">
        {shortcutGroups.map((group) => (
          <section
            aria-labelledby={`shortcut-${group.title}`}
            key={group.title}
          >
            <div className="mb-3 flex items-center gap-2">
              <Keyboard className="size-4 text-[var(--text-muted)]" />
              <h2
                className="text-sm font-semibold"
                id={`shortcut-${group.title}`}
              >
                {group.title}
              </h2>
            </div>
            <dl className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
              {group.shortcuts.map((shortcut) => (
                <div
                  className="flex items-center justify-between gap-4 border-b border-[var(--border)] px-4 py-3 last:border-b-0"
                  key={shortcut.description}
                >
                  <dt className="text-sm">{shortcut.description}</dt>
                  <dd className="flex shrink-0 items-center gap-1">
                    {shortcut.keys.map((key) => (
                      <kbd
                        className="min-w-7 rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-subtle)] px-2 py-1 text-center font-mono text-xs text-[var(--text-muted)] shadow-sm"
                        key={key}
                      >
                        {key}
                      </kbd>
                    ))}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </div>
  );
}
