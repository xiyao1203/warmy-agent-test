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
      className={`group relative overflow-hidden rounded-[var(--radius)] border border-[var(--hairline)] bg-[var(--surface)] p-6 transition-all duration-300 hover:border-[var(--primary)] hover:shadow-lg hover:shadow-[var(--primary)]/10 ${className}`}
      {...props}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary)]/5 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="relative">
        {icon && (
          <div className="mb-4 inline-flex rounded-lg bg-[var(--primary-subtle)] p-2.5 text-[var(--primary)] transition-transform duration-300 group-hover:scale-110">
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
