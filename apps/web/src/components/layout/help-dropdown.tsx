"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
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

const menuItems = [
  {
    description: "产品使用文档和 API 参考",
    href: "/docs",
    icon: BookOpen,
    label: "帮助文档",
  },
  {
    description: "测试用例编写规范与最佳实践",
    href: "/docs/test-cases",
    icon: FileText,
    label: "测试指南",
  },
  {
    description: "功能演示和操作教程",
    href: "/docs/tutorials",
    icon: Video,
    label: "视频教程",
  },
  {
    description: "常用操作快捷键一览",
    href: "/docs/shortcuts",
    icon: Keyboard,
    label: "键盘快捷键",
  },
  {
    description: "提交问题或功能建议",
    href: "/feedback",
    icon: MessageSquare,
    label: "反馈建议",
  },
];

const externalItems = [
  {
    href: "https://github.com/xiyao1203/warmy-agent-test",
    label: "GitHub 仓库",
  },
  {
    href: "https://github.com/xiyao1203/warmy-agent-test/blob/main/CHANGELOG.md",
    label: "更新日志",
  },
];

export function HelpDropdown() {
  return (
    <DropdownMenuPrimitive.Root>
      <DropdownMenuPrimitive.Trigger asChild>
        <button aria-label="帮助中心" className="app-icon-button" type="button">
          <HelpCircle aria-hidden="true" className="size-4" />
        </button>
      </DropdownMenuPrimitive.Trigger>
      <DropdownMenuPrimitive.Portal>
        <DropdownMenuPrimitive.Content
          align="end"
          aria-label="帮助中心"
          className="app-menu w-72"
          sideOffset={7}
        >
          <DropdownMenuPrimitive.Label className="border-b border-[var(--hairline)] px-3 py-2.5">
            <span className="block text-sm font-semibold">帮助中心</span>
            <span className="mt-0.5 block text-xs font-normal text-[var(--muted)]">
              获取帮助、学习最佳实践
            </span>
          </DropdownMenuPrimitive.Label>
          <div className="py-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <DropdownMenuPrimitive.Item asChild key={item.label}>
                  <Link
                    className="app-menu-item min-h-12 px-3"
                    href={item.href}
                  >
                    <Icon
                      aria-hidden="true"
                      className="size-4 shrink-0 text-[var(--muted)]"
                    />
                    <span className="min-w-0">
                      <span className="block font-medium">{item.label}</span>
                      <span className="block truncate text-xs text-[var(--muted)]">
                        {item.description}
                      </span>
                    </span>
                  </Link>
                </DropdownMenuPrimitive.Item>
              );
            })}
          </div>
          <DropdownMenuPrimitive.Separator className="h-px bg-[var(--hairline)]" />
          <DropdownMenuPrimitive.Label className="px-3 py-2 text-xs font-medium text-[var(--muted)]">
            外部资源
          </DropdownMenuPrimitive.Label>
          {externalItems.map((item) => (
            <DropdownMenuPrimitive.Item asChild key={item.label}>
              <a
                className="app-menu-item px-3"
                href={item.href}
                rel="noopener noreferrer"
                target="_blank"
              >
                <ExternalLink aria-hidden="true" className="size-4" />
                {item.label}
                <span aria-hidden="true" className="ml-auto text-xs">
                  ↗
                </span>
              </a>
            </DropdownMenuPrimitive.Item>
          ))}
        </DropdownMenuPrimitive.Content>
      </DropdownMenuPrimitive.Portal>
    </DropdownMenuPrimitive.Root>
  );
}
