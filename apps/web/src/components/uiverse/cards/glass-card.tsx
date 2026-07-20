import type { HTMLAttributes } from "react";

import { Card } from "@/components/ui/card";

type GlassCardProps = HTMLAttributes<HTMLDivElement>;

export function GlassCard({ children, className, ...props }: GlassCardProps) {
  return (
    <Card className={className} {...props}>
      {children}
    </Card>
  );
}
