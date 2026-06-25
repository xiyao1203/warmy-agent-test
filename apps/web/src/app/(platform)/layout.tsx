import type { ReactNode } from "react";

import { PlatformFrame } from "@/components/layout/platform-frame";

export default function PlatformLayout({ children }: { children: ReactNode }) {
  return <PlatformFrame>{children}</PlatformFrame>;
}
