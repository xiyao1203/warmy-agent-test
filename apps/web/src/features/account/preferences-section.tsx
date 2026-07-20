"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Moon, RotateCcw, Save, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";

import { getUserSettings, updateUserSettings } from "./api";

const themes = [
  { id: "light", label: "浅色", icon: Sun },
  { id: "dark", label: "深色", icon: Moon },
] as const;

type ExplicitTheme = (typeof themes)[number]["id"];

function normalizeTheme(theme: string | null | undefined): ExplicitTheme {
  if (theme === "dark" || theme === "light") return theme;
  if (
    typeof document !== "undefined" &&
    document.documentElement.classList.contains("dark")
  ) {
    return "dark";
  }
  return "light";
}

const languages = [
  { id: "zh-CN", label: "简体中文" },
  { id: "en", label: "English" },
] as const;

export function PreferencesSection() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useQuery({
    queryKey: ["userSettings"],
    queryFn: getUserSettings,
  });

  const [themeDraft, setThemeDraft] = useState<ExplicitTheme | null>(null);
  const [languageDraft, setLanguageDraft] = useState<"zh-CN" | "en" | null>(
    null,
  );
  const theme = themeDraft ?? normalizeTheme(settings?.theme);
  const language = languageDraft ?? settings?.language ?? "zh-CN";
  const hasChanges = themeDraft !== null || languageDraft !== null;

  const mutation = useMutation({
    mutationFn: updateUserSettings,
    onSuccess: (newSettings) => {
      queryClient.setQueryData(["userSettings"], newSettings);
      setThemeDraft(null);
      setLanguageDraft(null);
    },
  });

  function handleThemeChange(newTheme: ExplicitTheme) {
    setThemeDraft(newTheme);
  }

  function handleLanguageChange(newLanguage: "zh-CN" | "en") {
    setLanguageDraft(newLanguage);
  }

  function handleReset() {
    setThemeDraft(null);
    setLanguageDraft(null);
  }

  function handleSave() {
    mutation.mutate({ theme, language });
  }

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[var(--hairline)] bg-[var(--card)] p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-24 rounded bg-[var(--muted)]" />
          <div className="h-20 w-full rounded bg-[var(--muted)]" />
          <div className="h-20 w-full rounded bg-[var(--muted)]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <section className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-4 sm:p-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold">外观主题</h3>
          <p className="mt-1 text-xs text-[var(--muted)]">
            选择平台界面的显示方式。
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {themes.map(({ id, label, icon: Icon }) => (
            <button
              aria-pressed={theme === id}
              key={id}
              className={`flex items-center justify-center gap-2 rounded-[var(--radius-md)] border p-3 transition-colors ${
                theme === id
                  ? "border-[var(--primary)] bg-[var(--primary-subtle)]"
                  : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
              }`}
              onClick={() => handleThemeChange(id)}
              type="button"
            >
              <Icon className="size-4" />
              <span className="text-sm font-medium">{label}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-4 sm:p-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold">语言设置</h3>
          <p className="mt-1 text-xs text-[var(--muted)]">
            设置界面和系统消息使用的语言。
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {languages.map(({ id, label }) => (
            <button
              aria-pressed={language === id}
              key={id}
              className={`flex items-center justify-center gap-2 rounded-[var(--radius-md)] border p-3 transition-colors ${
                language === id
                  ? "border-[var(--primary)] bg-[var(--primary-subtle)]"
                  : "border-[var(--hairline)] hover:bg-[var(--canvas-soft)]"
              }`}
              onClick={() => handleLanguageChange(id)}
              type="button"
            >
              <span className="text-sm font-medium">{label}</span>
            </button>
          ))}
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        <Button
          className="gap-2"
          disabled={!hasChanges || mutation.isPending}
          onClick={handleSave}
        >
          <Save className="size-4" />
          {mutation.isPending ? "保存中..." : "保存设置"}
        </Button>
        <Button
          className="gap-2"
          disabled={!hasChanges}
          onClick={handleReset}
          variant="secondary"
        >
          <RotateCcw className="size-4" />
          重置
        </Button>
      </div>

      {mutation.isError && (
        <div
          className="rounded-md bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]"
          role="alert"
        >
          保存失败，请重试
        </div>
      )}
    </div>
  );
}
