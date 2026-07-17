"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { Check, Laptop, Moon, Sun } from "lucide-react";
import { useEffect, useMemo, useSyncExternalStore } from "react";

type ThemePreference = "dark" | "light" | "system";
type ResolvedTheme = "dark" | "light";

const STORAGE_KEY = "theme";
const SYSTEM_QUERY = "(prefers-color-scheme: dark)";
const THEME_CHANGE_EVENT = "warmy:theme-change";

function isThemePreference(value: string | null): value is ThemePreference {
  return value === "dark" || value === "light" || value === "system";
}

function getStoredPreference(): ThemePreference {
  if (typeof window === "undefined") return "system";
  const value = localStorage.getItem(STORAGE_KEY);
  return isThemePreference(value) ? value : "system";
}

function resolveTheme(preference: ThemePreference): ResolvedTheme {
  if (preference !== "system") return preference;
  return window.matchMedia(SYSTEM_QUERY).matches ? "dark" : "light";
}

function subscribeToPreference(onStoreChange: () => void) {
  const handleStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY) onStoreChange();
  };
  window.addEventListener(THEME_CHANGE_EVENT, onStoreChange);
  window.addEventListener("storage", handleStorage);
  return () => {
    window.removeEventListener(THEME_CHANGE_EVENT, onStoreChange);
    window.removeEventListener("storage", handleStorage);
  };
}

export function applyThemePreference(preference: ThemePreference) {
  const resolved = resolveTheme(preference);
  const root = document.documentElement;
  root.classList.remove("dark", "light");
  root.classList.add(resolved);
  root.dataset.theme = resolved;
  root.dataset.themePreference = preference;
  root.style.colorScheme = resolved;
}

const options: Array<{
  icon: typeof Sun;
  label: string;
  value: ThemePreference;
}> = [
  { icon: Sun, label: "浅色", value: "light" },
  { icon: Moon, label: "深色", value: "dark" },
  { icon: Laptop, label: "跟随系统", value: "system" },
];

export function ThemeToggle({ className = "" }: { className?: string }) {
  const preference = useSyncExternalStore<ThemePreference>(
    subscribeToPreference,
    getStoredPreference,
    () => "system",
  );
  const ActiveIcon = useMemo(
    () => options.find((option) => option.value === preference)?.icon ?? Laptop,
    [preference],
  );

  useEffect(() => {
    applyThemePreference(preference);
    if (preference !== "system") return;

    const media = window.matchMedia(SYSTEM_QUERY);
    const handleChange = () => applyThemePreference("system");
    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, [preference]);

  function selectTheme(value: ThemePreference) {
    localStorage.setItem(STORAGE_KEY, value);
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
    applyThemePreference(value);
  }

  return (
    <DropdownMenuPrimitive.Root>
      <DropdownMenuPrimitive.Trigger asChild>
        <button
          aria-label="外观设置"
          className={`app-icon-button ${className}`}
          title="外观设置"
          type="button"
        >
          <ActiveIcon aria-hidden="true" className="size-4" />
        </button>
      </DropdownMenuPrimitive.Trigger>
      <DropdownMenuPrimitive.Portal>
        <DropdownMenuPrimitive.Content
          align="end"
          aria-label="主题"
          className="app-menu w-40"
          sideOffset={7}
        >
          <DropdownMenuPrimitive.Label className="px-2 py-1.5 text-xs font-medium text-[var(--muted)]">
            界面外观
          </DropdownMenuPrimitive.Label>
          <DropdownMenuPrimitive.RadioGroup
            onValueChange={(value) => {
              if (isThemePreference(value)) selectTheme(value);
            }}
            value={preference}
          >
            {options.map((option) => {
              const Icon = option.icon;
              return (
                <DropdownMenuPrimitive.RadioItem
                  aria-label={option.label}
                  className="app-menu-item"
                  key={option.value}
                  value={option.value}
                >
                  <Icon aria-hidden="true" className="size-4" />
                  <span className="flex-1">{option.label}</span>
                  <DropdownMenuPrimitive.ItemIndicator>
                    <Check aria-hidden="true" className="size-4" />
                  </DropdownMenuPrimitive.ItemIndicator>
                </DropdownMenuPrimitive.RadioItem>
              );
            })}
          </DropdownMenuPrimitive.RadioGroup>
        </DropdownMenuPrimitive.Content>
      </DropdownMenuPrimitive.Portal>
    </DropdownMenuPrimitive.Root>
  );
}
