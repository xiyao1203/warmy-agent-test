import { Suspense } from "react";
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
    <AccountCenter>
      <Suspense fallback={<div className="p-8 text-center">加载中...</div>}>
        <SectionContent section={section} />
      </Suspense>
    </AccountCenter>
  );
}
