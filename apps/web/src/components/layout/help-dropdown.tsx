"use client";

import {
  BookOpen,
  ExternalLink,
  FileText,
  HelpCircle,
  Keyboard,
  MessageSquare,
} from "lucide-react";
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
      description: "查看使用文档和指南",
      href: "/docs",
      icon: <BookOpen className="size-4" />,
      label: "帮助文档",
    },
    {
      description: "查看测试用例编写规范",
      href: "/docs/test-cases",
      icon: <FileText className="size-4" />,
      label: "测试指南",
    },
    {
      description: "查看键盘快捷键",
      href: "#shortcuts",
      icon: <Keyboard className="size-4" />,
      label: "键盘快捷键",
    },
    {
      description: "提交反馈或建议",
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
        className="grid size-8 place-items-center rounded-[var(--radius-sm)] text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <HelpCircle aria-hidden="true" className="size-4" />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 min-w-[16rem] rounded-lg border border-[var(--border)] bg-[var(--surface)] py-1 shadow-lg">
          <div className="border-b border-[var(--border)] px-3 py-2">
            <p className="text-sm font-medium">帮助中心</p>
            <p className="text-xs text-[var(--text-muted)]">
              获取帮助和资源
            </p>
          </div>
          {menuItems.map((item) => (
            <a
              className="flex items-start gap-3 px-3 py-2 text-sm transition-colors hover:bg-[var(--surface-subtle)]"
              href={item.href}
              key={item.label}
              onClick={() => setOpen(false)}
            >
              <span className="mt-0.5 text-[var(--text-muted)]">
                {item.icon}
              </span>
              <div>
                <p className="font-medium">{item.label}</p>
                <p className="text-xs text-[var(--text-muted)]">
                  {item.description}
                </p>
              </div>
            </a>
          ))}
          <div className="border-t border-[var(--border)]" />
          <a
            className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-subtle)] hover:text-[var(--text)]"
            href="https://github.com/your-repo"
            onClick={() => setOpen(false)}
            rel="noopener noreferrer"
            target="_blank"
          >
            <ExternalLink className="size-4" />
            GitHub 仓库
          </a>
        </div>
      )}
    </div>
  );
}
