import type { ReactNode } from "react";

import { HelpShell } from "@/features/help";

export default function HelpLayout({ children }: { children: ReactNode }) {
  return <HelpShell>{children}</HelpShell>;
}
