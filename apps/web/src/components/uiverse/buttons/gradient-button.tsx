import type { ComponentProps } from "react";

import { Button } from "@/components/ui/button";

type GradientButtonProps = ComponentProps<typeof Button>;

export function GradientButton({
  children,
  className = "",
  loading = false,
  ...props
}: GradientButtonProps) {
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
