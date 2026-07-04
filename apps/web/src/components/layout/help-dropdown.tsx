"use client";

import {
  BookOpen,
  ExternalLink,
  FileText,
  HelpCircle,
  Keyboard,
  MessageSquare,
  Video,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export function HelpDropdown() {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const menuItems = [
    {
      description: "产品使用文档和 API 参考",
      href: "/docs",
      icon: <BookOpen className="size-4" />,
      label: "帮助文档",
    },
    {
      description: "测试用例编写规范与最佳实践",
      href: "/docs/test-cases",
      icon: <FileText className="size-4" />,
      label: "测试指南",
    },
    {
      description: "功能演示和操作教程",
      href: "/docs/tutorials",
      icon: <Video className="size-4" />,
      label: "视频教程",
    },
    {
      description: "常用操作快捷键一览",
      href: "/docs/shortcuts",
      icon: <Keyboard className="size-4" />,
      label: "键盘快捷键",
    },
    {
      description: "提交问题或功能建议",
      href: "/feedback",
      icon: <MessageSquare className="size-4" />,
      label: "反馈建议",
    },
  ];

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        aria-expanded={open}
        aria-haspopup="true"
        aria-label="帮助中心"
        className="grid size-8 place-items-center rounded-[var(--radius-md)] text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <HelpCircle aria-hidden="true" className="size-4" />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 min-w-[18rem] rounded-lg border border-[var(--hairline)] bg-[var(--surface)] py-1">
          <div className="border-b border-[var(--hairline)] px-4 py-3">
            <p className="text-sm font-semibold">帮助中心</p>
            <p className="mt-0.5 text-xs text-[var(--muted)]">
              获取帮助、学习最佳实践
            </p>
          </div>
          {menuItems.map((item) => (
            <Link
              className="flex items-start gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-[var(--canvas-soft)]"
              href={item.href}
              key={item.label}
              onClick={() => setOpen(false)}
            >
              <span className="mt-0.5 text-[var(--muted)]">{item.icon}</span>
              <div>
                <p className="font-medium">{item.label}</p>
                <p className="text-xs text-[var(--muted)]">
                  {item.description}
                </p>
              </div>
            </Link>
          ))}
          <div className="border-t border-[var(--hairline)]" />
          <div className="px-4 py-2">
            <p className="text-xs font-medium text-[var(--muted)]">外部资源</p>
          </div>
          <a
            className="flex items-center gap-2 px-4 py-2 text-sm text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
            href="https://github.com/xiyao1203/warmy-agent-test"
            onClick={() => setOpen(false)}
            rel="noopener noreferrer"
            target="_blank"
          >
            <ExternalLink className="size-4" />
            GitHub 仓库
            <span className="ml-auto text-xs text-[var(--body)]">↗</span>
          </a>
          <a
            className="flex items-center gap-2 px-4 py-2 text-sm text-[var(--muted)] transition-colors hover:bg-[var(--canvas-soft)] hover:text-[var(--ink)]"
            href="https://github.com/xiyao1203/warmy-agent-test/blob/main/CHANGELOG.md"
            onClick={() => setOpen(false)}
            rel="noopener noreferrer"
            target="_blank"
          >
            <ExternalLink className="size-4" />
            更新日志
            <span className="ml-auto text-xs text-[var(--body)]">↗</span>
          </a>
        </div>
      )}
    </div>
  );
}
