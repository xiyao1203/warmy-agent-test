import type { ResourceReference } from "@warmy/generated-api-client";
import Link from "next/link";

import { Badge } from "./badge";

const SAFE_PROJECT_PATH = /^\/projects\/[A-Za-z0-9-]+(?:\/[A-Za-z0-9._~-]+)*$/;

export function ResourceReferenceLink({
  emptyLabel = "暂无数据",
  reference,
}: {
  emptyLabel?: string;
  reference?: ResourceReference | null;
}) {
  if (!reference) {
    return <span className="text-[var(--muted)]">{emptyLabel}</span>;
  }

  const content = (
    <span className="inline-flex min-w-0 flex-wrap items-center gap-1.5">
      <span className="truncate">{reference.name}</span>
      {reference.version != null ? (
        <Badge tone="neutral">v{reference.version}</Badge>
      ) : null}
      {reference.status ? (
        <span className="text-xs text-[var(--muted)]">{reference.status}</span>
      ) : null}
    </span>
  );

  if (reference.href && SAFE_PROJECT_PATH.test(reference.href)) {
    return (
      <Link
        className="inline-flex max-w-full text-[var(--primary)] hover:underline"
        href={reference.href}
      >
        {content}
      </Link>
    );
  }

  return content;
}
