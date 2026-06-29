"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Mail, Save } from "lucide-react";

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
    <div className="flex items-center justify-between rounded-lg border border-[var(--border)] p-4">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-sm text-[var(--text-muted)]">{description}</p>
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

  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(false);
  const [testCompleteNotifications, setTestCompleteNotifications] =
    useState(true);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (settings) {
      setEmailNotifications(settings.email_notifications);
      setPushNotifications(settings.push_notifications);
      setTestCompleteNotifications(settings.test_complete_notifications);
    }
  }, [settings]);

  const mutation = useMutation({
    mutationFn: updateUserSettings,
    onSuccess: (newSettings) => {
      queryClient.setQueryData(["userSettings"], newSettings);
      setHasChanges(false);
    },
  });

  function handleToggle(
    setter: React.Dispatch<React.SetStateAction<boolean>>,
    value: boolean
  ) {
    setter(value);
    setHasChanges(true);
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
    <div className="space-y-6">
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-6">
        <h3 className="mb-4 text-lg font-medium">通知偏好</h3>
        <div className="space-y-3">
          <NotificationToggle
            description="接收测试结果、系统更新等邮件通知"
            enabled={emailNotifications}
            label="邮件通知"
            onChange={(value) => handleToggle(setEmailNotifications, value)}
          />
          <NotificationToggle
            description="接收浏览器推送通知"
            enabled={pushNotifications}
            label="推送通知"
            onChange={(value) => handleToggle(setPushNotifications, value)}
          />
          <NotificationToggle
            description="测试计划执行完成后通知"
            enabled={testCompleteNotifications}
            label="测试完成通知"
            onChange={(value) =>
              handleToggle(setTestCompleteNotifications, value)
            }
          />
        </div>
      </div>

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
        <div className="rounded-md bg-[var(--danger-subtle)] p-3 text-sm text-[var(--danger)]">
          保存失败，请重试
        </div>
      )}
    </div>
  );
}
