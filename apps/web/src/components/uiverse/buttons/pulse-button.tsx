"use client";

import type { ComponentProps } from "react";

import { Button } from "@/components/ui/button";

type PulseButtonProps = ComponentProps<typeof Button>;

export function PulseButton({
  children,
  className = "",
  loading = false,
  ...props
}: PulseButtonProps) {
  return (
    <Button
      className={className}
      loading={loading}
      variant="primary"
      {...props}
    >
      {children}
    </Button>
  );
}
