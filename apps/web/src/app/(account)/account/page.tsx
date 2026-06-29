import { Suspense } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import {
  AccountCenter,
  NotificationsSection,
  PreferencesSection,
  ProfileSection,
  SecuritySection,
  normalizeAccountSection,
  type AccountSection,
} from "@/features/account";

function SectionContent({ section }: { section: AccountSection }) {
  switch (section) {
    case "profile":
      return <ProfileSection />;
    case "preferences":
      return <PreferencesSection />;
    case "notifications":
      return <NotificationsSection />;
    case "security":
      return <SecuritySection />;
  }
}

export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<{ section?: string }>;
}) {
  const { section } = await searchParams;
  const activeSection = normalizeAccountSection(section);

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-[1040px] items-center justify-between px-4 sm:px-6">
          <Link
            className="flex items-center gap-2 text-sm font-semibold transition-colors hover:text-[var(--accent)]"
            href="/projects"
          >
            <ArrowLeft className="size-4" />
            返回应用
          </Link>
          <span className="text-sm font-semibold">账户中心</span>
          <div className="w-20" />
        </div>
      </header>

      <AccountCenter>
        <Suspense fallback={<div className="p-8 text-center">加载中...</div>}>
          <SectionContent section={activeSection} />
        </Suspense>
      </AccountCenter>
    </div>
  );
}
