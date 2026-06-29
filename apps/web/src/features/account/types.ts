import type { UserResponse } from "@warmy/generated-api-client";

export type AccountSection =
  | "profile"
  | "preferences"
  | "notifications"
  | "security";

export interface AccountNavItem {
  id: AccountSection;
  label: string;
  href: string;
  description: string;
}

export const accountSections: ReadonlyArray<AccountNavItem> = [
  {
    id: "profile",
    label: "个人资料",
    href: "/account?section=profile",
    description: "管理您的基本信息和头像",
  },
  {
    id: "preferences",
    label: "偏好设置",
    href: "/account?section=preferences",
    description: "自定义主题、语言等偏好",
  },
  {
    id: "notifications",
    label: "通知设置",
    href: "/account?section=notifications",
    description: "管理邮件和推送通知",
  },
  {
    id: "security",
    label: "账号安全",
    href: "/account?section=security",
    description: "密码管理和安全设置",
  },
];

export function normalizeAccountSection(
  value: string | null | undefined,
): AccountSection {
  return accountSections.some((section) => section.id === value)
    ? (value as AccountSection)
    : "profile";
}

export type EditableProfile = Pick<UserResponse, "display_name" | "email">;
