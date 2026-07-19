import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function ListToolbar({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex min-h-14 items-center gap-3 border-y border-[var(--hairline)] py-3 max-[760px]:flex-col max-[760px]:items-stretch",
        className,
      )}
      {...props}
    />
  );
}
