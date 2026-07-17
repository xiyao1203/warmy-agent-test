import type { HTMLAttributes, ReactNode } from "react";

type HoverCardProps = HTMLAttributes<HTMLDivElement> & {
  icon?: ReactNode;
  title: string;
  description?: string;
  value?: string | number;
};

export function HoverCard({
  className = "",
  description,
  icon,
  title,
  value,
  ...props
}: HoverCardProps) {
  return (
    <div
      className={`group relative overflow-hidden rounded-[var(--radius)] border border-[var(--hairline)] bg-[var(--surface)] p-6 transition-colors duration-300 hover:border-[var(--primary)] ${className}`}
      {...props}
    >
      <div className="relative">
        {icon && (
          <div className="mb-4 inline-flex rounded-lg bg-[var(--primary-subtle)] p-2.5 text-[var(--primary)]">
            {icon}
          </div>
        )}
        <h3 className="text-sm font-medium text-[var(--muted)]">{title}</h3>
        {value !== undefined && (
          <p className="mt-2 text-3xl font-bold text-[var(--ink)]">{value}</p>
        )}
        {description && (
          <p className="mt-2 text-sm text-[var(--muted)]">{description}</p>
        )}
      </div>
    </div>
  );
}
