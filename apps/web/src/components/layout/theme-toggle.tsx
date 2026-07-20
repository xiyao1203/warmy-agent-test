"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useSyncExternalStore } from "react";

import { Tooltip } from "@/components/uiverse";

type ThemePreference = "dark" | "light";

const STORAGE_KEY = "theme";
const SYSTEM_QUERY = "(prefers-color-scheme: dark)";
const THEME_CHANGE_EVENT = "warmy:theme-change";

function isThemePreference(value: string | null): value is ThemePreference {
  return value === "dark" || value === "light";
}

function getStoredPreference(): ThemePreference {
  if (typeof window === "undefined") return "light";
  const value = localStorage.getItem(STORAGE_KEY);
  if (isThemePreference(value)) return value;
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
  const root = document.documentElement;
  root.classList.remove("dark", "light");
  root.classList.add(preference);
  root.dataset.theme = preference;
  root.dataset.themePreference = preference;
  root.style.colorScheme = preference;
}

export function ThemeToggle({ className = "" }: { className?: string }) {
  const preference = useSyncExternalStore<ThemePreference>(
    subscribeToPreference,
    getStoredPreference,
    () => "light",
  );
  const nextPreference: ThemePreference =
    preference === "light" ? "dark" : "light";
  const actionLabel = nextPreference === "dark" ? "切换至深色" : "切换至浅色";
  const ActiveIcon = preference === "dark" ? Moon : Sun;

  useEffect(() => {
    if (!isThemePreference(localStorage.getItem(STORAGE_KEY))) {
      localStorage.setItem(STORAGE_KEY, preference);
    }
    applyThemePreference(preference);
  }, [preference]);

  function selectTheme(value: ThemePreference) {
    localStorage.setItem(STORAGE_KEY, value);
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
    applyThemePreference(value);
  }

  return (
    <Tooltip content={actionLabel} side="bottom">
      <button
        aria-label={actionLabel}
        className={`app-icon-button ${className}`}
        onClick={() => selectTheme(nextPreference)}
        title={actionLabel}
        type="button"
      >
        <ActiveIcon
          aria-hidden="true"
          className="theme-toggle-icon size-4"
          key={preference}
        />
      </button>
    </Tooltip>
  );
}
