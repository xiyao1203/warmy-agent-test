"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bell,
  Globe,
  Moon,
  Palette,
  Sun,
  User,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { getCurrentUser } from "@/features/auth";

const themes = [
  { description: "跟随系统设置", icon: <Globe className="size-4" />, value: "system" },
  { description: "浅色主题", icon: <Sun className="size-4" />, value: "light" },
  { description: "深色主题", icon: <Moon className="size-4" />, value: "dark" },
];

const languages = [
  { label: "简体中文", value: "zh-CN" },
  { label: "English", value: "en" },
];

export default function SettingsPage() {
  const userQuery = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
  });
  const user = userQuery.data;
  const [theme, setTheme] = useState("system");
  const [language, setLanguage] = useState("zh-CN");
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    testComplete: true,
  });

  if (!user) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <p className="text-sm text-[var(--text-muted)]">加载中...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[800px] px-6 py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">设置</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          管理您的偏好设置和通知选项
        </p>
      </header>

      {/* 外观设置 */}
      <section className="mb-8 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-6 py-4">
          <div className="flex items-center gap-2">
            <Palette className="size-5 text-[var(--text-muted)]" />
            <h3 className="font-semibold">外观</h3>
          </div>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            自定义界面主题和显示偏好
          </p>
        </div>
        <div className="p-6">
          <label className="mb-3 block text-sm font-medium">主题</label>
          <div className="grid gap-3 sm:grid-cols-3">
            {themes.map((item) => (
              <button
                className={`flex items-center gap-3 rounded-lg border px-4 py-3 text-sm transition-all ${
                  theme === item.value
                    ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                    : "border-[var(--border)] hover:border-[var(--border-strong)]"
                }`}
                key={item.value}
                onClick={() => setTheme(item.value)}
              >
                {item.icon}
                <div className="text-left">
                  <p className="font-medium">{item.value === "system" ? "跟随系统" : item.value === "light" ? "浅色" : "深色"}</p>
                  <p className="text-xs text-[var(--text-muted)]">{item.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* 语言设置 */}
      <section className="mb-8 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-6 py-4">
          <div className="flex items-center gap-2">
            <Globe className="size-5 text-[var(--text-muted)]" />
            <h3 className="font-semibold">语言</h3>
          </div>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            选择界面显示语言
          </p>
        </div>
        <div className="p-6">
          <div className="flex gap-3">
            {languages.map((item) => (
              <button
                className={`rounded-lg border px-4 py-2 text-sm transition-all ${
                  language === item.value
                    ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)] font-medium"
                    : "border-[var(--border)] hover:border-[var(--border-strong)]"
                }`}
                key={item.value}
                onClick={() => setLanguage(item.value)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* 通知设置 */}
      <section className="mb-8 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-6 py-4">
          <div className="flex items-center gap-2">
            <Bell className="size-5 text-[var(--text-muted)]" />
            <h3 className="font-semibold">通知</h3>
          </div>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            管理您接收通知的方式和类型
          </p>
        </div>
        <div className="divide-y divide-[var(--border)]">
          <div className="flex items-center justify-between px-6 py-4">
            <div>
              <p className="font-medium">邮件通知</p>
              <p className="text-sm text-[var(--text-muted)]">
                通过邮件接收重要通知
              </p>
            </div>
            <button
              className={`relative h-6 w-11 rounded-full transition-colors ${
                notifications.email ? "bg-[var(--accent)]" : "bg-[var(--border)]"
              }`}
              onClick={() =>
                setNotifications((prev) => ({ ...prev, email: !prev.email }))
              }
            >
              <span
                className={`absolute left-0.5 top-0.5 size-5 rounded-full bg-white shadow-sm transition-transform ${
                  notifications.email ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between px-6 py-4">
            <div>
              <p className="font-medium">推送通知</p>
              <p className="text-sm text-[var(--text-muted)]">
                接收浏览器推送通知
              </p>
            </div>
            <button
              className={`relative h-6 w-11 rounded-full transition-colors ${
                notifications.push ? "bg-[var(--accent)]" : "bg-[var(--border)]"
              }`}
              onClick={() =>
                setNotifications((prev) => ({ ...prev, push: !prev.push }))
              }
            >
              <span
                className={`absolute left-0.5 top-0.5 size-5 rounded-full bg-white shadow-sm transition-transform ${
                  notifications.push ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between px-6 py-4">
            <div>
              <p className="font-medium">测试完成通知</p>
              <p className="text-sm text-[var(--text-muted)]">
                测试计划执行完成时通知您
              </p>
            </div>
            <button
              className={`relative h-6 w-11 rounded-full transition-colors ${
                notifications.testComplete ? "bg-[var(--accent)]" : "bg-[var(--border)]"
              }`}
              onClick={() =>
                setNotifications((prev) => ({
                  ...prev,
                  testComplete: !prev.testComplete,
                }))
              }
            >
              <span
                className={`absolute left-0.5 top-0.5 size-5 rounded-full bg-white shadow-sm transition-transform ${
                  notifications.testComplete ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>
      </section>

      {/* 保存按钮 */}
      <div className="flex justify-end gap-3">
        <Button variant="ghost">重置</Button>
        <Button variant="primary">保存设置</Button>
      </div>
    </div>
  );
}
