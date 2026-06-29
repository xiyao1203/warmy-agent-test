import { Suspense } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { AccountCenter } from "@/features/account/account-center";
import { ProfileSection } from "@/features/account/profile-section";
import { PreferencesSection } from "@/features/account/preferences-section";
import { NotificationsSection } from "@/features/account/notifications-section";
import { SecuritySection } from "@/features/account/security-section";

function SectionContent({ section }: { section: string }) {
  switch (section) {
    case "profile":
      return <ProfileSection />;
    case "preferences":
      return <PreferencesSection />;
    case "notifications":
      return <NotificationsSection />;
    case "security":
      return <SecuritySection />;
    default:
      return <ProfileSection />;
  }
}

export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<{ section?: string }>;
}) {
  const { section = "profile" } = await searchParams;

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
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
          <SectionContent section={section} />
        </Suspense>
      </AccountCenter>
    </div>
  );
}
