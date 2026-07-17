"use client";

import type { HTMLAttributes, ReactNode } from "react";

type ListCardProps = HTMLAttributes<HTMLLIElement> & {
  title: string;
  description?: string;
  badge?: ReactNode;
  actions?: ReactNode;
  footer?: ReactNode;
};

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
      className={`group rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 transition-colors hover:border-[var(--hairline-strong)] hover:bg-[var(--canvas-soft)] ${className}`}
      {...props}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-semibold text-[var(--ink)]">
              {title}
            </h3>
            {badge}
          </div>
          {description ? (
            <p className="mt-1 truncate text-xs text-[var(--muted)]">
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
  value: string | number;
  label: string;
};

export function ListCardStat({ label, value }: ListCardStatProps) {
  return (
    <div className="flex items-baseline gap-1.5">
      <span className="text-sm font-semibold text-[var(--ink)]">{value}</span>
      <span className="text-xs text-[var(--muted)]">{label}</span>
    </div>
  );
}

type ListCardMetaProps = HTMLAttributes<HTMLDivElement> & {
  items: (string | undefined)[];
  separator?: string;
};

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
      className={`mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-[var(--muted)] ${className}`}
      {...props}
    >
      {filtered.map((item, index) => (
        <span className="flex items-center gap-2" key={index}>
          {index > 0 ? (
            <span className="text-[var(--body)]">{separator}</span>
          ) : null}
          {item}
        </span>
      ))}
    </div>
  );
}
