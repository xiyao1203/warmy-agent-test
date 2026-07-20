"use client";

import type { HTMLAttributes, ReactNode } from "react";

type ListCardProps = HTMLAttributes<HTMLLIElement> & {
  actions?: ReactNode;
  badge?: ReactNode;
  description?: string;
  footer?: ReactNode;
  icon?: ReactNode;
  title: string;
  tone?: "accent" | "danger" | "info" | "neutral" | "success" | "warning";
};

export function ListCard({
  actions,
  badge,
  className = "",
  description,
  footer,
  icon,
  title,
  tone = "neutral",
  ...props
}: ListCardProps) {
  return (
    <li
      className={`precision-list-card group rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-4 py-3 transition-[background,border-color,box-shadow,transform] duration-[var(--motion-fast)] hover:border-[var(--hairline-strong)] hover:bg-[var(--canvas-soft)] focus-within:border-[var(--hairline-strong)] ${className}`}
      data-tone={tone}
      {...props}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          {icon ? (
            <span className="precision-list-card-icon">{icon}</span>
          ) : null}
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
        </div>
        {actions ? (
          <div
            className="flex min-h-8 shrink-0 items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
            data-testid="list-card-actions"
          >
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
