"use client";

import type { HTMLAttributes, ReactNode } from "react";

type ListCardProps = HTMLAttributes<HTMLLIElement> & {
  /** 主标题 */
  title: string;
  /** 副标题或描述 */
  description?: string;
  /** 标题右侧的状态徽章 */
  badge?: ReactNode;
  /** 右侧操作区域 */
  actions?: ReactNode;
  /** 底部扩展内容 */
  footer?: ReactNode;
};

/**
 * 极简风格列表卡片组件
 *
 * 遵循方案1设计规范：
 * - 高信息密度、低视觉噪声
 * - 中性色为主，依靠排版和间距建立层级
 * - 无渐变、玻璃拟态或装饰性动画
 * - hover 时使用细微背景色变化
 */
export function ListCard({
  actions,
  badge,
  className = "",
  description,
  footer,
  title,
  ...props
}: ListCardProps) {
  return (
    <li
      className={`group rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] px-5 py-4 transition-colors hover:bg-[var(--surface-subtle)] ${className}`}
      {...props}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-semibold text-[var(--text)]">
              {title}
            </h3>
            {badge}
          </div>
          {description ? (
            <p className="mt-1 truncate text-xs text-[var(--text-muted)]">
              {description}
            </p>
          ) : null}
        </div>
        {actions ? (
          <div className="flex shrink-0 items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
            {actions}
          </div>
        ) : null}
      </div>
      {footer}
    </li>
  );
}

type ListCardStatProps = {
  /** 统计数值 */
  value: string | number;
  /** 统计标签 */
  label: string;
};

/**
 * 卡片内统计指标
 */
export function ListCardStat({ label, value }: ListCardStatProps) {
  return (
    <div className="flex items-baseline gap-1.5">
      <span className="text-sm font-semibold text-[var(--text)]">{value}</span>
      <span className="text-xs text-[var(--text-muted)]">{label}</span>
    </div>
  );
}

type ListCardMetaProps = HTMLAttributes<HTMLDivElement> & {
  /** 元数据项列表 */
  items: (string | undefined)[];
  /** 分隔符，默认为 "·" */
  separator?: string;
};

/**
 * 卡片内元数据行
 */
export function ListCardMeta({
  className = "",
  items,
  separator = "·",
  ...props
}: ListCardMetaProps) {
  const filtered = items.filter(Boolean);
  if (!filtered.length) return null;

  return (
    <div
      className={`mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-[var(--text-muted)] ${className}`}
      {...props}
    >
      {filtered.map((item, index) => (
        <span className="flex items-center gap-2" key={index}>
          {index > 0 ? (
            <span className="text-[var(--text-subtle)]">{separator}</span>
          ) : null}
          {item}
        </span>
      ))}
    </div>
  );
}
