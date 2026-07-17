"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import type {
  ProjectResponse,
  UserResponse,
} from "@warmy/generated-api-client";
import {
  Activity,
  Blocks,
  Bot,
  Check,
  ChevronRight,
  ClipboardCheck,
  Gauge,
  GitCompareArrows,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  Menu,
  Monitor,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { logout } from "@/features/auth";
import { ProjectSwitcher } from "@/features/projects";
import { canManageUsers } from "@/lib/permissions";
import { projectOverviewPath, projectWorkspacePath } from "@/lib/routes";

import { BrandMark } from "./brand-mark";
import { HelpDropdown } from "./help-dropdown";
import { NotificationDropdown } from "./notification-dropdown";
import { ThemeToggle } from "./theme-toggle";
import { UserDropdown } from "./user-dropdown";

type AppShellProps = {
  children: ReactNode;
  currentProjectId?: string;
  onProjectSelect: (projectId: string) => void;
  projects: ProjectResponse[];
  user: UserResponse;
  workspaceMode?: "agent" | "management";
};

type NavigationItem = {
  exact?: boolean;
  href: string;
  icon: LucideIcon;
  label: string;
};

type NavigationGroup = {
  items: NavigationItem[];
  label: string;
};

const MOBILE_QUERY = "(max-width: 759px)";

export function initialSidebarCollapsed(
  viewportWidth: number,
  storedPreference: string | null,
) {
  return viewportWidth >= 760 && storedPreference === "true";
}

function projectNavigation(projectId: string): NavigationGroup[] {
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

export function AppShell({
  children,
  currentProjectId,
  onProjectSelect,
  projects,
  user,
  workspaceMode = "management",
}: AppShellProps) {
  const pathname = usePathname();
  const activeProjectId =
    currentProjectId || (projects.length > 0 ? projects[0].id : null);
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);

  useEffect(() => {
    function restoreCollapsePreference() {
      setCollapsed(
        initialSidebarCollapsed(
          window.innerWidth,
          localStorage.getItem("sidebar-collapsed"),
        ),
      );
    }
    restoreCollapsePreference();
  }, []);

  useEffect(() => {
    const media = window.matchMedia(MOBILE_QUERY);
    const update = () => {
      setMobile(media.matches);
      if (!media.matches) setMobileNavigationOpen(false);
    };
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((value) => !value);
      }
    }
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  const groups = useMemo(
    () => (activeProjectId ? projectNavigation(activeProjectId) : []),
    [activeProjectId],
  );
  const items = useMemo(
    () => [
      { exact: true, href: "/projects", icon: Blocks, label: "项目列表" },
      ...groups.flatMap((group) => group.items),
      ...(canManageUsers(user)
        ? [
            {
              href: "/system/users",
              icon: Users,
              label: "用户与权限",
            },
          ]
        : []),
    ],
    [groups, user],
  );
  const activeItem = items.find((item) => isRouteActive(pathname, item));

  const toggleSidebar = useCallback(() => {
    setCollapsed((value) => {
      const next = !value;
      localStorage.setItem("sidebar-collapsed", String(next));
      return next;
    });
  }, []);

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div className="flex min-w-0 items-center gap-2">
          {mobile ? (
            <button
              aria-label="打开导航"
              className="app-icon-button"
              onClick={() => setMobileNavigationOpen(true)}
              type="button"
            >
              <Menu aria-hidden="true" className="size-4" />
            </button>
          ) : null}
          <Link
            aria-label="Warmy Agent Test"
            className="app-brand"
            href="/login"
          >
            <BrandMark compact />
            <span className="max-sm:hidden">Warmy</span>
          </Link>
          <div className="h-4 w-px bg-[var(--hairline)] max-sm:hidden" />
          <ProjectSwitcher
            currentProjectId={currentProjectId}
            onSelect={onProjectSelect}
            projects={projects}
          />
          <Breadcrumb currentLabel={activeItem?.label} />
        </div>

        <div className="flex shrink-0 items-center gap-1">
          <button
            aria-label="全局搜索"
            className="app-search-trigger"
            onClick={() => setCommandOpen(true)}
            type="button"
          >
            <Search aria-hidden="true" className="size-4" />
            <span className="max-lg:hidden">搜索</span>
            <kbd className="max-lg:hidden">⌘ K</kbd>
          </button>
          <QuickCreate projectId={activeProjectId} />
          {activeProjectId ? (
            <Link
              aria-label="查看运行中心"
              className="app-status-indicator max-md:hidden"
              href={`/projects/${activeProjectId}/runs`}
            >
              <Activity aria-hidden="true" className="size-3.5" />
              运行中心
            </Link>
          ) : null}
          <ThemeToggle />
          <HelpDropdown />
          <NotificationDropdown />
          <UserDropdown
            displayName={user.display_name}
            email={user.email}
            onLogout={async () => {
              await logout();
              window.location.assign("/login");
            }}
          />
        </div>
      </header>

      <div className="app-body">
        <aside
          className="app-sidebar max-[759px]:hidden"
          data-collapsed={collapsed}
          style={{
            width: collapsed
              ? "var(--sidebar-width-collapsed)"
              : "var(--sidebar-width)",
          }}
        >
          <Navigation
            collapsed={collapsed}
            groups={groups}
            onNavigate={undefined}
            pathname={pathname}
            showUsers={canManageUsers(user)}
          />
          <button
            aria-expanded={!collapsed}
            aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
            className="app-nav-link mt-auto w-full"
            onClick={toggleSidebar}
            title={collapsed ? "展开侧边栏" : "收起侧边栏"}
            type="button"
          >
            {collapsed ? (
              <PanelLeftOpen aria-hidden="true" className="size-4" />
            ) : (
              <PanelLeftClose aria-hidden="true" className="size-4" />
            )}
            {!collapsed ? <span>收起菜单</span> : null}
          </button>
        </aside>

        <main className="app-main" data-workspace-mode={workspaceMode}>
          {children}
        </main>
      </div>

      <MobileNavigation
        groups={groups}
        onOpenChange={setMobileNavigationOpen}
        open={mobileNavigationOpen}
        pathname={pathname}
        showUsers={canManageUsers(user)}
      />
      <CommandPalette
        items={items}
        onOpenChange={setCommandOpen}
        open={commandOpen}
      />
    </div>
  );
}

function Breadcrumb({ currentLabel }: { currentLabel?: string }) {
  if (!currentLabel || currentLabel === "项目列表") return null;
  return (
    <div
      aria-label="面包屑"
      className="ml-1 flex min-w-0 items-center gap-1 text-xs text-[var(--muted)] max-xl:hidden"
      role="navigation"
    >
      <ChevronRight aria-hidden="true" className="size-3.5" />
      <span className="max-w-36 truncate text-[var(--body)]">
        {currentLabel}
      </span>
    </div>
  );
}

function Navigation({
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
  return (
    <Link
      aria-current={active ? "page" : undefined}
      aria-label={item.label}
      className="app-nav-link"
      data-active={active}
      href={item.href}
      onClick={onNavigate}
      title={collapsed ? item.label : undefined}
    >
      <Icon
        aria-hidden="true"
        className="size-4 shrink-0 text-current"
        data-navigation-icon="monochrome"
      />
      {!collapsed ? <span className="truncate">{item.label}</span> : null}
    </Link>
  );
}

function QuickCreate({ projectId }: { projectId: string | null }) {
  if (!projectId) return null;
  const links = [
    { href: `/projects/${projectId}/datasets?create=dataset`, label: "用例集" },
    {
      href: `/projects/${projectId}/test-plans?create=plan`,
      label: "测试计划",
    },
    { href: `/projects/${projectId}/agents?create=agent`, label: "智能体" },
  ];
  return (
    <DropdownMenuPrimitive.Root>
      <DropdownMenuPrimitive.Trigger asChild>
        <button
          aria-label="快速创建"
          className="app-create-button"
          type="button"
        >
          <Plus aria-hidden="true" className="size-4" />
          <span className="max-md:hidden">新建</span>
        </button>
      </DropdownMenuPrimitive.Trigger>
      <DropdownMenuPrimitive.Portal>
        <DropdownMenuPrimitive.Content
          align="end"
          aria-label="快速创建"
          className="app-menu w-44"
          sideOffset={7}
        >
          <DropdownMenuPrimitive.Label className="px-2 py-1.5 text-xs text-[var(--muted)]">
            创建测试资产
          </DropdownMenuPrimitive.Label>
          {links.map((link) => (
            <DropdownMenuPrimitive.Item asChild key={link.href}>
              <Link className="app-menu-item" href={link.href}>
                <Plus aria-hidden="true" className="size-4" />
                {link.label}
              </Link>
            </DropdownMenuPrimitive.Item>
          ))}
        </DropdownMenuPrimitive.Content>
      </DropdownMenuPrimitive.Portal>
    </DropdownMenuPrimitive.Root>
  );
}

function MobileNavigation({
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

function CommandPalette({
  items,
  onOpenChange,
  open,
}: {
  items: NavigationItem[];
  onOpenChange: (open: boolean) => void;
  open: boolean;
}) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const filtered = items.filter((item) =>
    item.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()),
  );

  function openActiveItem() {
    const item = filtered[activeIndex];
    if (!item) return;
    router.push(item.href);
    onOpenChange(false);
    setQuery("");
    setActiveIndex(0);
  }

  return (
    <DialogPrimitive.Root
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) {
          setQuery("");
          setActiveIndex(0);
        }
      }}
      open={open}
    >
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="app-overlay" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className="app-command-palette"
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            inputRef.current?.focus();
          }}
        >
          <DialogPrimitive.Title className="sr-only">
            全局搜索
          </DialogPrimitive.Title>
          <div className="flex items-center gap-2 border-b border-[var(--hairline)] px-4">
            <Search aria-hidden="true" className="size-4 text-[var(--muted)]" />
            <input
              aria-activedescendant={
                filtered.length ? `command-option-${activeIndex}` : undefined
              }
              aria-controls="command-results"
              aria-label="全局搜索"
              aria-autocomplete="list"
              autoFocus
              className="h-12 min-w-0 flex-1 bg-transparent text-sm text-[var(--ink)] placeholder:text-[var(--muted)]"
              onChange={(event) => {
                setQuery(event.target.value);
                setActiveIndex(0);
              }}
              onKeyDown={(event) => {
                if (!filtered.length) return;
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setActiveIndex((index) => (index + 1) % filtered.length);
                } else if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setActiveIndex(
                    (index) => (index - 1 + filtered.length) % filtered.length,
                  );
                } else if (event.key === "Home") {
                  event.preventDefault();
                  setActiveIndex(0);
                } else if (event.key === "End") {
                  event.preventDefault();
                  setActiveIndex(filtered.length - 1);
                } else if (event.key === "Enter") {
                  event.preventDefault();
                  openActiveItem();
                }
              }}
              placeholder="搜索平台页面…"
              ref={inputRef}
              role="searchbox"
              value={query}
            />
            <kbd>ESC</kbd>
          </div>
          <div className="max-h-[min(26rem,60vh)] overflow-y-auto p-2">
            {filtered.length ? (
              <div aria-label="搜索结果" id="command-results" role="listbox">
                {filtered.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      aria-label={item.label}
                      aria-selected={index === activeIndex}
                      className="app-command-item"
                      data-active={index === activeIndex}
                      href={item.href}
                      id={`command-option-${index}`}
                      key={item.href}
                      onClick={() => {
                        onOpenChange(false);
                        setQuery("");
                        setActiveIndex(0);
                      }}
                      onMouseMove={() => setActiveIndex(index)}
                      role="option"
                    >
                      <Icon aria-hidden="true" className="size-4" />
                      <span>{item.label}</span>
                      <ChevronRight
                        aria-hidden="true"
                        className="ml-auto size-4 text-[var(--muted-soft)]"
                      />
                    </Link>
                  );
                })}
              </div>
            ) : (
              <div className="grid min-h-24 place-items-center text-sm text-[var(--muted)]">
                没有匹配的页面
              </div>
            )}
          </div>
          <div className="flex items-center justify-between border-t border-[var(--hairline)] px-4 py-2 text-xs text-[var(--muted)]">
            <span>快速前往平台任意核心模块</span>
            <span>回车打开</span>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

function isRouteActive(
  pathname: string,
  item: Pick<NavigationItem, "exact" | "href">,
) {
  return item.exact
    ? pathname === item.href
    : pathname === item.href || pathname.startsWith(`${item.href}/`);
}
