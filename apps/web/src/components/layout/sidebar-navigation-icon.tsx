import type { LucideIcon } from "lucide-react";

export const navigationTones = [
  "amber",
  "blue",
  "coral",
  "indigo",
  "mint",
] as const;

export type NavigationTone = (typeof navigationTones)[number];

export function SidebarNavigationIcon({
  icon: Icon,
  tone,
}: {
  icon: LucideIcon;
  tone: NavigationTone;
}) {
  return (
    <span className="app-nav-icon" data-navigation-icon-carrier>
      <span
        className="app-nav-icon-artwork"
        data-navigation-icon="chromatic-signal"
        data-navigation-tone={tone}
      >
        <Icon aria-hidden="true" className="app-nav-icon-glyph" />
        <span aria-hidden="true" data-navigation-signal />
      </span>
    </span>
  );
}
