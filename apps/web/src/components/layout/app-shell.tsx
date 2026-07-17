"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import type {
  ProjectResponse,
  UserResponse,
} from "@warmy/generated-api-client";
import {
  Activity,
  Blocks,
  ChevronRight,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { logout } from "@/features/auth";
import { ProjectSwitcher } from "@/features/projects";
import { canManageUsers } from "@/lib/permissions";

import { BrandMark } from "./brand-mark";
import { CommandPalette } from "./app-shell-command";
import {
  initialSidebarCollapsed,
  isRouteActive,
  MOBILE_QUERY,
  MobileNavigation,
  Navigation,
  projectNavigation,
} from "./app-shell-navigation";
import { HelpDropdown } from "./help-dropdown";
import { NotificationDropdown } from "./notification-dropdown";
import { ThemeToggle } from "./theme-toggle";
import { UserDropdown } from "./user-dropdown";

export { initialSidebarCollapsed } from "./app-shell-navigation";

type AppShellProps = {
  children: ReactNode;
  currentProjectId?: string;
  onProjectSelect: (projectId: string) => void;
  projects: ProjectResponse[];
  user: UserResponse;
  workspaceMode?: "agent" | "management";
};

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
