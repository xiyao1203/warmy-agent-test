import type { ReactNode } from "react";

export function EmptyState({
  action,
  description,
  title,
  visual,
}: {
  action?: ReactNode;
  description: string;
  title: string;
  visual?: ReactNode;
}) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center px-6 py-10 text-center">
      {visual ? <div className="mb-5">{visual}</div> : null}
      <h2 className="text-sm font-semibold text-[var(--ink)]">{title}</h2>
      <p className="mt-1 max-w-md text-sm leading-6 text-[var(--muted)]">
        {description}
      </p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
