import {
  GraduationCap,
  Keyboard,
  LifeBuoy,
  ListChecks,
  MessageSquare,
  Rocket,
  type LucideIcon,
} from "lucide-react";

export interface HelpNavigationItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const helpNavigation: ReadonlyArray<HelpNavigationItem> = [
  { href: "/docs", label: "帮助首页", icon: LifeBuoy },
  { href: "/docs#quickstart", label: "快速开始", icon: Rocket },
  { href: "/docs/test-cases", label: "测试用例", icon: ListChecks },
  { href: "/docs/tutorials", label: "教程", icon: GraduationCap },
  { href: "/docs/shortcuts", label: "快捷键", icon: Keyboard },
  { href: "/feedback", label: "反馈", icon: MessageSquare },
];

export function isHelpDestinationActive(pathname: string, href: string) {
  if (href.includes("#")) {
    return false;
  }

  if (href === "/docs") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}
