import type { CSSProperties, ReactNode } from "react";

export type SidebarIconName =
  | "agent"
  | "browser-profile"
  | "environment"
  | "experiment"
  | "model"
  | "overview"
  | "release-gate"
  | "review"
  | "scorer"
  | "security"
  | "test-agent"
  | "test-case"
  | "test-plan"
  | "test-run"
  | "user-management";

export type SidebarIconTone =
  | "amber"
  | "azure"
  | "cyan"
  | "emerald"
  | "fuchsia"
  | "green"
  | "indigo"
  | "orange"
  | "purple"
  | "red"
  | "rose"
  | "sky"
  | "slate-blue"
  | "teal"
  | "violet";

type SidebarIconStyle = CSSProperties & {
  "--sidebar-icon-cool": string;
  "--sidebar-icon-deep": string;
  "--sidebar-icon-hot": string;
  "--sidebar-icon-mist": string;
  "--sidebar-icon-soft": string;
};

const sidebarIconToneStyles = {
  amber: {
    "--sidebar-icon-cool": "#5B7CFA",
    "--sidebar-icon-deep": "#8A4B00",
    "--sidebar-icon-hot": "#FFB224",
    "--sidebar-icon-mist": "#FFE6A5",
    "--sidebar-icon-soft": "#FFF3C8",
  },
  azure: {
    "--sidebar-icon-cool": "#14C8F5",
    "--sidebar-icon-deep": "#0756CF",
    "--sidebar-icon-hot": "#8B5CF6",
    "--sidebar-icon-mist": "#BAEAFE",
    "--sidebar-icon-soft": "#DBF6FF",
  },
  cyan: {
    "--sidebar-icon-cool": "#35D3F4",
    "--sidebar-icon-deep": "#087990",
    "--sidebar-icon-hot": "#3B82F6",
    "--sidebar-icon-mist": "#B8F4FF",
    "--sidebar-icon-soft": "#E4FBFF",
  },
  emerald: {
    "--sidebar-icon-cool": "#34D399",
    "--sidebar-icon-deep": "#047857",
    "--sidebar-icon-hot": "#10B981",
    "--sidebar-icon-mist": "#B9F8D4",
    "--sidebar-icon-soft": "#E7FBF0",
  },
  fuchsia: {
    "--sidebar-icon-cool": "#8B5CF6",
    "--sidebar-icon-deep": "#86198F",
    "--sidebar-icon-hot": "#E879F9",
    "--sidebar-icon-mist": "#F5D0FE",
    "--sidebar-icon-soft": "#FDF0FF",
  },
  green: {
    "--sidebar-icon-cool": "#22C55E",
    "--sidebar-icon-deep": "#3F7A12",
    "--sidebar-icon-hot": "#A3E635",
    "--sidebar-icon-mist": "#C7F9A6",
    "--sidebar-icon-soft": "#F0FCE7",
  },
  indigo: {
    "--sidebar-icon-cool": "#6366F1",
    "--sidebar-icon-deep": "#3730A3",
    "--sidebar-icon-hot": "#A78BFA",
    "--sidebar-icon-mist": "#C7D2FE",
    "--sidebar-icon-soft": "#EEF2FF",
  },
  orange: {
    "--sidebar-icon-cool": "#F97316",
    "--sidebar-icon-deep": "#9A3412",
    "--sidebar-icon-hot": "#FDBA32",
    "--sidebar-icon-mist": "#FED7AA",
    "--sidebar-icon-soft": "#FFF1E6",
  },
  purple: {
    "--sidebar-icon-cool": "#7C3AED",
    "--sidebar-icon-deep": "#5B21B6",
    "--sidebar-icon-hot": "#C084FC",
    "--sidebar-icon-mist": "#DDD6FE",
    "--sidebar-icon-soft": "#F3EEFF",
  },
  red: {
    "--sidebar-icon-cool": "#F97316",
    "--sidebar-icon-deep": "#991B1B",
    "--sidebar-icon-hot": "#FB3F4A",
    "--sidebar-icon-mist": "#FECACA",
    "--sidebar-icon-soft": "#FFF0F0",
  },
  rose: {
    "--sidebar-icon-cool": "#F472B6",
    "--sidebar-icon-deep": "#9F1239",
    "--sidebar-icon-hot": "#FB7185",
    "--sidebar-icon-mist": "#FFE4E6",
    "--sidebar-icon-soft": "#FFF1F5",
  },
  sky: {
    "--sidebar-icon-cool": "#38BDF8",
    "--sidebar-icon-deep": "#075985",
    "--sidebar-icon-hot": "#60A5FA",
    "--sidebar-icon-mist": "#BAE6FD",
    "--sidebar-icon-soft": "#EAF6FF",
  },
  "slate-blue": {
    "--sidebar-icon-cool": "#8EA4C2",
    "--sidebar-icon-deep": "#334155",
    "--sidebar-icon-hot": "#60A5FA",
    "--sidebar-icon-mist": "#CBD5E1",
    "--sidebar-icon-soft": "#EEF4FF",
  },
  teal: {
    "--sidebar-icon-cool": "#2DD4BF",
    "--sidebar-icon-deep": "#0F766E",
    "--sidebar-icon-hot": "#5EEAD4",
    "--sidebar-icon-mist": "#99F6E4",
    "--sidebar-icon-soft": "#E9FBF7",
  },
  violet: {
    "--sidebar-icon-cool": "#7C3AED",
    "--sidebar-icon-deep": "#5B21B6",
    "--sidebar-icon-hot": "#C084FC",
    "--sidebar-icon-mist": "#DDD6FE",
    "--sidebar-icon-soft": "#F2EEFF",
  },
} satisfies Record<SidebarIconTone, SidebarIconStyle>;

const iconArtwork = {
  agent: () => (
    <>
      <path
        d="M7.5 15.5c0-5 3.6-8.8 8.5-8.8s8.5 3.8 8.5 8.8-3.6 8.8-8.5 8.8-8.5-3.8-8.5-8.8Z"
        fill="var(--sidebar-icon-soft)"
      />
      <circle cx="12.1" cy="13.1" fill="var(--sidebar-icon-hot)" r="3.5" />
      <circle cx="19.9" cy="13.1" fill="var(--sidebar-icon-cool)" r="3.5" />
      <path
        d="M10.4 19.7c2.1-2.6 4.1-3.6 6-3.2 2.3.5 3.7 3.2 5.2 5.8-3.5 2.3-8.4 2.1-11.2-2.6Z"
        fill="var(--sidebar-icon-deep)"
      />
      <rect
        fill="var(--sidebar-icon-mist)"
        height="3.8"
        rx="1.9"
        width="12"
        x="10"
        y="9"
      />
    </>
  ),
  "browser-profile": () => (
    <>
      <rect
        fill="var(--sidebar-icon-soft)"
        height="18"
        rx="4"
        width="22"
        x="5"
        y="7"
      />
      <rect
        fill="var(--sidebar-icon-hot)"
        height="5"
        rx="2.5"
        width="22"
        x="5"
        y="7"
      />
      <circle cx="20" cy="17" fill="var(--sidebar-icon-cool)" r="5.2" />
      <path
        d="M20 12c1.6 1.3 2.4 3 2.4 5s-.8 3.7-2.4 5c-1.6-1.3-2.4-3-2.4-5s.8-3.7 2.4-5Z"
        fill="var(--sidebar-icon-mist)"
      />
      <rect
        fill="var(--sidebar-icon-deep)"
        height="4"
        rx="1.2"
        width="7"
        x="8.5"
        y="15"
      />
    </>
  ),
  environment: () => (
    <>
      <path
        d="M16 4.5 25 8v6.6c0 5.9-3.5 10.4-9 12.9-5.5-2.5-9-7-9-12.9V8l9-3.5Z"
        fill="var(--sidebar-icon-soft)"
      />
      <path
        d="M16 7.5 22 10v4.6c0 4-2.1 7-6 9-3.9-2-6-5-6-9V10l6-2.5Z"
        fill="var(--sidebar-icon-cool)"
      />
      <path
        d="m12.2 15.9 2.4 2.4 5.2-6.2 2 1.7-7 8.2-4.3-4.2 1.7-1.9Z"
        fill="var(--sidebar-icon-deep)"
      />
      <circle cx="22.4" cy="8.6" fill="var(--sidebar-icon-hot)" r="2.8" />
      <rect
        fill="var(--sidebar-icon-mist)"
        height="4"
        rx="2"
        width="8"
        x="12"
        y="12"
      />
    </>
  ),
  experiment: () => (
    <>
      <circle cx="10" cy="10" fill="var(--sidebar-icon-soft)" r="5" />
      <circle cx="22" cy="10" fill="var(--sidebar-icon-hot)" r="4.5" />
      <circle cx="16" cy="22" fill="var(--sidebar-icon-cool)" r="5.3" />
      <path
        d="M12.7 11.3h6.7l-3.2 7.8-3.5-7.8Z"
        fill="var(--sidebar-icon-mist)"
      />
      <path
        d="M9.7 9.1h12.7v2.5H19l-2.7 8.1h-2.8l2.8-8.1H9.7V9.1Z"
        fill="var(--sidebar-icon-deep)"
      />
    </>
  ),
  model: () => (
    <>
      <rect
        fill="var(--sidebar-icon-soft)"
        height="5"
        rx="2.5"
        width="20"
        x="6"
        y="7"
      />
      <rect
        fill="var(--sidebar-icon-hot)"
        height="5"
        rx="2.5"
        width="16"
        x="10"
        y="14"
      />
      <rect
        fill="var(--sidebar-icon-cool)"
        height="5"
        rx="2.5"
        width="19"
        x="6"
        y="21"
      />
      <circle cx="12" cy="9.5" fill="var(--sidebar-icon-deep)" r="3.2" />
      <circle cx="22" cy="16.5" fill="var(--sidebar-icon-mist)" r="3.2" />
    </>
  ),
  overview: () => (
    <>
      <circle cx="16" cy="16" fill="var(--sidebar-icon-soft)" r="11" />
      <path d="M16 5a11 11 0 0 1 11 11H16V5Z" fill="var(--sidebar-icon-hot)" />
      <path
        d="M16 16h11a11 11 0 0 1-15.6 10L16 16Z"
        fill="var(--sidebar-icon-cool)"
      />
      <path
        d="M16 16 11.4 26A11 11 0 0 1 16 5v11Z"
        fill="var(--sidebar-icon-deep)"
      />
      <circle cx="16" cy="16" fill="var(--sidebar-icon-mist)" r="4.2" />
    </>
  ),
  "release-gate": () => (
    <>
      <path
        d="M16 4.5 25.5 10v11L16 27.5 6.5 21V10L16 4.5Z"
        fill="var(--sidebar-icon-soft)"
      />
      <path
        d="M16 7.7 22.5 11.5v7.8L16 23.4l-6.5-4.1v-7.8L16 7.7Z"
        fill="var(--sidebar-icon-cool)"
      />
      <path
        d="m12.1 16.5 2.7 2.6 5.6-6.5 2 1.7-7.4 8.4-4.7-4.4 1.8-1.8Z"
        fill="var(--sidebar-icon-deep)"
      />
      <rect
        fill="var(--sidebar-icon-hot)"
        height="8"
        rx="2"
        width="4"
        x="7"
        y="12"
      />
      <circle cx="24" cy="9.2" fill="var(--sidebar-icon-mist)" r="3" />
    </>
  ),
  review: () => (
    <>
      <path
        d="M6 10.5c0-2.5 2-4.5 4.5-4.5h3v3h-3A1.5 1.5 0 0 0 9 10.5v3H6v-3Zm12.5-4.5h3A4.5 4.5 0 0 1 26 10.5v3h-3v-3A1.5 1.5 0 0 0 21.5 9h-3V6ZM6 18.5h3v3A1.5 1.5 0 0 0 10.5 23h3v3h-3A4.5 4.5 0 0 1 6 21.5v-3Zm17 0h3v3a4.5 4.5 0 0 1-4.5 4.5h-3v-3h3a1.5 1.5 0 0 0 1.5-1.5v-3Z"
        fill="var(--sidebar-icon-soft)"
      />
      <circle cx="15" cy="15" fill="var(--sidebar-icon-hot)" r="5.2" />
      <path
        d="m18.5 18.5 5.4 5.4-2.5 2.5-5.4-5.4 2.5-2.5Z"
        fill="var(--sidebar-icon-deep)"
      />
      <rect
        fill="var(--sidebar-icon-cool)"
        height="3"
        rx="1.5"
        width="9"
        x="10.5"
        y="13.5"
      />
      <circle cx="15" cy="15" fill="var(--sidebar-icon-mist)" r="2.4" />
    </>
  ),
  scorer: () => (
    <>
      <path
        d="M6 20a10 10 0 1 1 20 0h-5a5 5 0 1 0-10 0H6Z"
        fill="var(--sidebar-icon-soft)"
      />
      <path
        d="M8 20a8 8 0 0 1 13.7-5.7l-3.3 3.4A3.5 3.5 0 0 0 12.5 20H8Z"
        fill="var(--sidebar-icon-hot)"
      />
      <path
        d="m16 18 7-6 1.8 2.1-6.7 6.2L16 18Z"
        fill="var(--sidebar-icon-deep)"
      />
      <circle cx="16" cy="20" fill="var(--sidebar-icon-cool)" r="3.2" />
      <rect
        fill="var(--sidebar-icon-mist)"
        height="3"
        rx="1.5"
        width="11"
        x="10.5"
        y="22.5"
      />
    </>
  ),
  security: () => (
    <>
      <path
        d="M16 4.5 25 8.5V15c0 5.7-3.5 10-9 12.4C10.5 25 7 20.7 7 15V8.5l9-4Z"
        fill="var(--sidebar-icon-soft)"
      />
      <path
        d="M16 7.5 22 10v4.9c0 3.7-2.1 6.5-6 8.6-3.9-2.1-6-4.9-6-8.6V10l6-2.5Z"
        fill="var(--sidebar-icon-hot)"
      />
      <rect
        fill="var(--sidebar-icon-deep)"
        height="8"
        rx="2"
        width="9"
        x="11.5"
        y="14"
      />
      <circle cx="16" cy="13.5" fill="var(--sidebar-icon-cool)" r="3.6" />
      <rect
        fill="var(--sidebar-icon-mist)"
        height="5"
        rx="1.2"
        width="2.6"
        x="14.7"
        y="16"
      />
    </>
  ),
  "test-agent": () => (
    <>
      <path
        d="M8 9.5A5.5 5.5 0 0 1 13.5 4h5A5.5 5.5 0 0 1 24 9.5v6A5.5 5.5 0 0 1 18.5 21H17l-5 5v-5.1A5.5 5.5 0 0 1 8 15.5v-6Z"
        fill="var(--sidebar-icon-soft)"
      />
      <rect
        fill="var(--sidebar-icon-cool)"
        height="10"
        rx="3"
        width="15"
        x="8.5"
        y="9"
      />
      <path
        d="M12.5 6.5h7l1.8 3.4H10.7l1.8-3.4Z"
        fill="var(--sidebar-icon-hot)"
      />
      <circle cx="13" cy="14" fill="var(--sidebar-icon-deep)" r="1.7" />
      <circle cx="19" cy="14" fill="var(--sidebar-icon-mist)" r="1.7" />
    </>
  ),
  "test-case": () => (
    <>
      <path
        d="M9 5.5h10l5 5v15H9a3 3 0 0 1-3-3v-14a3 3 0 0 1 3-3Z"
        fill="var(--sidebar-icon-soft)"
      />
      <path d="M19 5.5v5h5l-5-5Z" fill="var(--sidebar-icon-hot)" />
      <rect
        fill="var(--sidebar-icon-cool)"
        height="3"
        rx="1.5"
        width="11"
        x="10"
        y="14"
      />
      <rect
        fill="var(--sidebar-icon-deep)"
        height="3"
        rx="1.5"
        width="8"
        x="10"
        y="19"
      />
      <circle cx="10" cy="10" fill="var(--sidebar-icon-mist)" r="2.2" />
    </>
  ),
  "test-plan": () => (
    <>
      <rect
        fill="var(--sidebar-icon-soft)"
        height="20"
        rx="4"
        width="18"
        x="7"
        y="7"
      />
      <rect
        fill="var(--sidebar-icon-hot)"
        height="5"
        rx="2.5"
        width="10"
        x="11"
        y="4"
      />
      <rect
        fill="var(--sidebar-icon-cool)"
        height="3"
        rx="1.5"
        width="10"
        x="12"
        y="13"
      />
      <rect
        fill="var(--sidebar-icon-mist)"
        height="3"
        rx="1.5"
        width="8"
        x="12"
        y="19"
      />
      <path
        d="m9.5 13.9 1.2 1.2 2.7-3.1 1.4 1.2-4 4.5-2.5-2.4 1.2-1.4Z"
        fill="var(--sidebar-icon-deep)"
      />
    </>
  ),
  "test-run": () => (
    <>
      <rect
        fill="var(--sidebar-icon-soft)"
        height="19"
        rx="5"
        width="22"
        x="5"
        y="6.5"
      />
      <polygon fill="var(--sidebar-icon-hot)" points="14,12 22,16 14,20" />
      <circle cx="10" cy="21" fill="var(--sidebar-icon-cool)" r="3.2" />
      <rect
        fill="var(--sidebar-icon-deep)"
        height="3"
        rx="1.5"
        width="9"
        x="9"
        y="9"
      />
      <path
        d="M21 22c2.8-1.2 4.5-3 5.2-5.4.6 3.7-.8 6.5-4.2 8.5L21 22Z"
        fill="var(--sidebar-icon-mist)"
      />
    </>
  ),
  "user-management": () => (
    <>
      <circle cx="12.5" cy="11.5" fill="var(--sidebar-icon-soft)" r="5.5" />
      <path
        d="M5.5 26c1-5.4 3.7-8.1 8-8.1s7 2.7 8 8.1h-16Z"
        fill="var(--sidebar-icon-cool)"
      />
      <circle cx="22" cy="19" fill="var(--sidebar-icon-hot)" r="5" />
      <rect
        fill="var(--sidebar-icon-deep)"
        height="10"
        rx="1.8"
        width="3"
        x="20.5"
        y="14"
      />
      <circle cx="22" cy="19" fill="var(--sidebar-icon-mist)" r="2.1" />
    </>
  ),
} satisfies Record<SidebarIconName, () => ReactNode>;

export function SidebarColorIcon({
  name,
  tone,
}: {
  name: SidebarIconName;
  tone: SidebarIconTone;
}) {
  return (
    <svg
      aria-hidden="true"
      className="size-6 shrink-0 overflow-visible drop-shadow-[0_6px_10px_rgba(0,0,0,0.18)]"
      data-sidebar-icon={name}
      data-sidebar-icon-source="iconfont-cn-inspired"
      data-sidebar-icon-style="iconfont-color"
      data-sidebar-icon-tone={tone}
      focusable="false"
      style={sidebarIconToneStyles[tone]}
      viewBox="0 0 32 32"
    >
      {iconArtwork[name]()}
    </svg>
  );
}
