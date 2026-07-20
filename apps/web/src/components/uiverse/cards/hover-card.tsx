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
      className={`group relative overflow-hidden rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface-raised)] p-4 shadow-[var(--shadow-overlay)] transition-[border-color,box-shadow,transform] duration-[var(--motion-fast)] hover:border-[var(--hairline-strong)] ${className}`}
      {...props}
    >
      <div className="relative">
        {icon && (
          <div className="mb-3 inline-flex size-6 items-center justify-center text-[var(--muted)] [&_svg]:size-[var(--icon-optical-size)]">
            {icon}
          </div>
        )}
        <h3 className="text-sm font-medium text-[var(--muted)]">{title}</h3>
        {value !== undefined && (
          <p className="mt-2 text-xl font-semibold text-[var(--ink)]">
            {value}
          </p>
        )}
        {description && (
          <p className="mt-2 text-sm text-[var(--muted)]">{description}</p>
        )}
      </div>
    </div>
  );
}
