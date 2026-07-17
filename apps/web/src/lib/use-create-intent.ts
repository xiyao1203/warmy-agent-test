"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState } from "react";

export function useCreateIntent(kind: string) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const requested = searchParams.get("create") === kind;
  const [manuallyOpen, setManuallyOpen] = useState(false);
  const open = requested || manuallyOpen;

  const setOpenAndConsumeIntent = useCallback(
    (nextOpen: boolean) => {
      setManuallyOpen(nextOpen);
      if (nextOpen || !requested) return;

      const nextParams = new URLSearchParams(searchParams.toString());
      nextParams.delete("create");
      const query = nextParams.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, {
        scroll: false,
      });
    },
    [pathname, requested, router, searchParams],
  );

  return [open, setOpenAndConsumeIntent] as const;
}
