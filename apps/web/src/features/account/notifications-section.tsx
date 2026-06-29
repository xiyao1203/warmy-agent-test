"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";

import { Button } from "@/components/ui/button";

import { getUserSettings, updateUserSettings } from "./api";

interface NotificationToggleProps {
  label: string;
  description: string;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
}

function NotificationToggle({
  label,
  description,
  enabled,
  onChange,
}: NotificationToggleProps) {
  return (
    <div className="flex items-center justify-between gap-5 px-4 py-4">
      <div className="min-w-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="mt-1 text-xs leading-5 text-[var(--text-muted)]">
          {description}
        </p>
      </div>
      <button
        aria-checked={enabled}
        aria-label={label}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          enabled ? "bg-[var(--primary)]" : "bg-[var(--muted)]"
        }`}
        onClick={() => onChange(!enabled)}
        role="switch"
        type="button"
      >
        <span
          aria-hidden="true"
          className={`inline-block size-4 rounded-full bg-white transition-transform ${
            enabled ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}

export function NotificationsSection() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useQuery({
    queryKey: ["userSettings"],
    queryFn: getUserSettings,
  });

  const [emailDraft, setEmailDraft] = useState<boolean | null>(null);
  const [pushDraft, setPushDraft] = useState<boolean | null>(null);
  const [testCompleteDraft, setTestCompleteDraft] = useState<boolean | null>(
    null,
  );
  const emailNotifications =
    emailDraft ?? settings?.email_notifications ?? true;
  const pushNotifications = pushDraft ?? settings?.push_notifications ?? false;
  const testCompleteNotifications =
    testCompleteDraft ?? settings?.test_complete_notifications ?? true;
  const hasChanges =
    emailDraft !== null || pushDraft !== null || testCompleteDraft !== null;

  const mutation = useMutation({
    mutationFn: updateUserSettings,
    onSuccess: (newSettings) => {
      queryClient.setQueryData(["userSettings"], newSettings);
      setEmailDraft(null);
      setPushDraft(null);
      setTestCompleteDraft(null);
    },
  });

  function handleToggle(
    setter: React.Dispatch<React.SetStateAction<boolean | null>>,
    value: boolean,
  ) {
    setter(value);
  }

  function handleSave() {
    mutation.mutate({
      email_notifications: emailNotifications,
      push_notifications: pushNotifications,
      test_complete_notifications: testCompleteNotifications,
    });
  }

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-24 rounded bg-[var(--muted)]" />
          <div className="h-16 w-full rounded bg-[var(--muted)]" />
          <div className="h-16 w-full rounded bg-[var(--muted)]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <section className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] px-4 py-3">
          <h3 className="text-sm font-semibold">通知偏好</h3>
          <p className="mt-0.5 text-xs text-[var(--text-muted)]">
            选择需要接收的测试和系统消息。
          </p>
        </div>
        <div className="divide-y divide-[var(--border)]">
          <NotificationToggle
            description="接收测试结果、系统更新等邮件通知"
            enabled={emailNotifications}
            label="邮件通知"
            onChange={(value) => handleToggle(setEmailDraft, value)}
          />
          <NotificationToggle
            description="接收浏览器推送通知"
            enabled={pushNotifications}
            label="推送通知"
            onChange={(value) => handleToggle(setPushDraft, value)}
          />
          <NotificationToggle
            description="测试计划执行完成后通知"
            enabled={testCompleteNotifications}
            label="测试完成通知"
            onChange={(value) => handleToggle(setTestCompleteDraft, value)}
          />
        </div>
      </section>

      <div className="flex gap-2">
        <Button
          className="gap-2"
          disabled={!hasChanges || mutation.isPending}
          onClick={handleSave}
        >
          <Save className="size-4" />
          {mutation.isPending ? "保存中..." : "保存设置"}
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
