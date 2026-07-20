"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import {
  Activity,
  Blocks,
  Bot,
  Check,
  ClipboardCheck,
  Gauge,
  GitCompareArrows,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  Monitor,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { Tooltip } from "@/components/uiverse";
import { projectOverviewPath, projectWorkspacePath } from "@/lib/routes";

export type NavigationItem = {
  exact?: boolean;
  href: string;
  icon: LucideIcon;
  label: string;
};

export type NavigationGroup = {
  items: NavigationItem[];
  label: string;
};

export const MOBILE_QUERY = "(max-width: 759px)";

export function initialSidebarCollapsed(
  viewportWidth: number,
  storedPreference: string | null,
) {
  return viewportWidth >= 760 && storedPreference === "true";
}

export function projectNavigation(projectId: string): NavigationGroup[] {
  return [
    {
      label: "工作台",
      items: [
        {
          href: projectWorkspacePath(projectId),
          icon: Sparkles,
          label: "测试 Agent",
        },
        {
          href: projectOverviewPath(projectId),
          icon: LayoutDashboard,
          label: "概览",
        },
      ],
    },
    {
      label: "测试资产",
      items: [
        { href: `/projects/${projectId}/agents`, icon: Bot, label: "智能体" },
        {
          href: `/projects/${projectId}/datasets`,
          icon: ListChecks,
          label: "测试用例",
        },
        {
          href: `/projects/${projectId}/test-plans`,
          icon: ClipboardCheck,
          label: "测试计划",
        },
      ],
    },
    {
      label: "执行中心",
      items: [
        {
          href: `/projects/${projectId}/runs`,
          icon: Activity,
          label: "测试执行",
        },
        {
          href: `/projects/${projectId}/environments`,
          icon: KeyRound,
          label: "环境与凭证",
        },
        {
          href: `/projects/${projectId}/browser-profiles`,
          icon: Monitor,
          label: "浏览器实例",
        },
      ],
    },
    {
      label: "评测与治理",
      items: [
        {
          href: `/projects/${projectId}/scorers`,
          icon: Gauge,
          label: "评分器",
        },
        {
          href: `/projects/${projectId}/experiments`,
          icon: GitCompareArrows,
          label: "实验对比",
        },
        {
          href: `/projects/${projectId}/reviews`,
          icon: Check,
          label: "人工审核",
        },
        {
          href: `/projects/${projectId}/security`,
          icon: ShieldCheck,
          label: "安全测试",
        },
        {
          href: `/projects/${projectId}/gates`,
          icon: SlidersHorizontal,
          label: "发布门禁",
        },
      ],
    },
    {
      label: "系统设置",
      items: [
        {
          href: `/projects/${projectId}/models`,
          icon: Settings2,
          label: "模型配置",
        },
      ],
    },
  ];
}

export function Navigation({
  collapsed,
  groups,
  onNavigate,
  pathname,
  showUsers,
}: {
  collapsed: boolean;
  groups: NavigationGroup[];
  onNavigate?: () => void;
  pathname: string;
  showUsers: boolean;
}) {
  return (
    <nav aria-label="项目导航" className="app-navigation">
      <NavigationLink
        collapsed={collapsed}
        item={{
          exact: true,
          href: "/projects",
          icon: Blocks,
          label: "项目列表",
        }}
        onNavigate={onNavigate}
        pathname={pathname}
      />
      {groups.map((group) => (
        <div className="app-nav-group" key={group.label}>
          {!collapsed ? <p className="app-nav-label">{group.label}</p> : null}
          <div className="space-y-0.5">
            {group.items.map((item) => (
              <NavigationLink
                collapsed={collapsed}
                item={item}
                key={item.href}
                onNavigate={onNavigate}
                pathname={pathname}
              />
            ))}
          </div>
        </div>
      ))}
      {showUsers ? (
        <div className="app-nav-group border-t border-[var(--hairline)] pt-2">
          <NavigationLink
            collapsed={collapsed}
            item={{ href: "/system/users", icon: Users, label: "用户与权限" }}
            onNavigate={onNavigate}
            pathname={pathname}
          />
        </div>
      ) : null}
    </nav>
  );
}

function NavigationLink({
  collapsed,
  item,
  onNavigate,
  pathname,
}: {
  collapsed: boolean;
  item: NavigationItem;
  onNavigate?: () => void;
  pathname: string;
}) {
  const active = isRouteActive(pathname, item);
  const Icon = item.icon;
  const link = (
    <Link
      aria-current={active ? "page" : undefined}
      aria-label={item.label}
      className="app-nav-link"
      data-active={active}
      href={item.href}
      onClick={onNavigate}
    >
      <span className="app-nav-icon" data-navigation-icon-carrier>
        <Icon
          aria-hidden="true"
          className="shrink-0 text-current"
          data-navigation-icon="monochrome"
        />
      </span>
      {!collapsed ? <span className="truncate">{item.label}</span> : null}
    </Link>
  );

  if (!collapsed) return link;

  return (
    <Tooltip
      className="w-full justify-center"
      content={item.label}
      side="right"
    >
      {link}
    </Tooltip>
  );
}

export function MobileNavigation({
  groups,
  onOpenChange,
  open,
  pathname,
  showUsers,
}: {
  groups: NavigationGroup[];
  onOpenChange: (open: boolean) => void;
  open: boolean;
  pathname: string;
  showUsers: boolean;
}) {
  return (
    <DialogPrimitive.Root onOpenChange={onOpenChange} open={open}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="app-overlay" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className="app-mobile-navigation"
        >
          <div className="flex h-13 items-center justify-between border-b border-[var(--hairline)] px-4">
            <DialogPrimitive.Title className="text-sm font-semibold">
              项目导航
            </DialogPrimitive.Title>
            <DialogPrimitive.Close
              aria-label="关闭导航"
              className="app-icon-button"
            >
              <X aria-hidden="true" className="size-4" />
            </DialogPrimitive.Close>
          </div>
          <Navigation
            collapsed={false}
            groups={groups}
            onNavigate={() => onOpenChange(false)}
            pathname={pathname}
            showUsers={showUsers}
          />
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

export function isRouteActive(
  pathname: string,
  item: Pick<NavigationItem, "exact" | "href">,
) {
  return item.exact
    ? pathname === item.href
    : pathname === item.href || pathname.startsWith(`${item.href}/`);
}
