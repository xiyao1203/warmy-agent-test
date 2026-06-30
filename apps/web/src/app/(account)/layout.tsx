import type { ReactNode } from "react";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-[var(--background)]">{children}</div>;
}
