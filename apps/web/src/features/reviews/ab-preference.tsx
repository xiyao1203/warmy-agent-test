"use client";

import { Equal, ThumbsDown, ThumbsUp } from "lucide-react";

export type ABPreference = "a" | "b" | "equal";

export interface ABPreferenceOption {
  id: ABPreference;
  label: string;
  icon: typeof ThumbsUp;
  color: "success" | "danger" | "muted";
}

export interface ABPreferenceSelectorProps {
  /** 当前选中的偏好 */
  value: ABPreference | null;
  /** 偏好变更回调 */
  onChange: (preference: ABPreference) => void;
  /** 是否禁用 */
  disabled?: boolean;
}

const OPTIONS: ABPreferenceOption[] = [
  {
    id: "a",
    label: "A 更好",
    icon: ThumbsUp,
    color: "success",
  },
  {
    id: "equal",
    label: "相同",
    icon: Equal,
    color: "muted",
  },
  {
    id: "b",
    label: "B 更好",
    icon: ThumbsDown,
    color: "danger",
  },
];

const COLOR_MAP: Record<string, string> = {
  success: "text-[var(--success)]",
  danger: "text-[var(--danger)]",
  muted: "text-[var(--text-muted)]",
};

/**
 * A/B 偏好选择器组件。
 *
 * 用于人工审核时选择两个版本的偏好：
 * - A 更好
 * - B 更好
 * - 相同
 */
export function ABPreferenceSelector({
  value,
  onChange,
  disabled = false,
}: ABPreferenceSelectorProps) {
  return (
    <div className="flex gap-3" role="radiogroup" aria-label="A/B 偏好选择">
      {OPTIONS.map((option) => {
        const Icon = option.icon;
        const isSelected = value === option.id;

        return (
          <button
            key={option.id}
            className={`flex-1 rounded-lg border p-4 text-center transition-colors ${
              disabled
                ? "cursor-not-allowed opacity-50"
                : "cursor-pointer"
            } ${
              isSelected
                ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                : "border-[var(--border)] hover:bg-[var(--surface-subtle)]"
            }`}
            onClick={() => !disabled && onChange(option.id)}
            type="button"
            role="radio"
            aria-checked={isSelected}
            aria-disabled={disabled}
            disabled={disabled}
          >
            <Icon className={`mx-auto size-6 ${COLOR_MAP[option.color]}`} />
            <p className="mt-2 text-sm font-medium">{option.label}</p>
          </button>
        );
      })}
    </div>
  );
}

export interface ABReviewPanelProps {
  /** 版本 A 的输出内容 */
  outputA: string;
  /** 版本 B 的输出内容 */
  outputB: string;
  /** 当前选中的偏好 */
  preference: ABPreference | null;
  /** 偏好变更回调 */
  onPreferenceChange: (preference: ABPreference) => void;
  /** 审核意见 */
  opinion: string;
  /** 意见变更回调 */
  onOpinionChange: (opinion: string) => void;
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * A/B 偏好审核面板。
 *
 * 左右对比展示两个版本的输出，支持选择偏好。
 */
export function ABReviewPanel({
  outputA,
  outputB,
  preference,
  onPreferenceChange,
  opinion,
  onOpinionChange,
  disabled = false,
}: ABReviewPanelProps) {
  return (
    <div className="space-y-4">
      {/* 对比区域 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded border border-[var(--border)] p-4">
          <p className="mb-2 text-sm font-medium text-[var(--text-muted)]">
            版本 A
          </p>
          <div className="max-h-48 overflow-auto text-sm">{outputA}</div>
        </div>
        <div className="rounded border border-[var(--border)] p-4">
          <p className="mb-2 text-sm font-medium text-[var(--text-muted)]">
            版本 B
          </p>
          <div className="max-h-48 overflow-auto text-sm">{outputB}</div>
        </div>
      </div>

      {/* 偏好选择 */}
      <div>
        <p className="mb-3 text-sm font-medium">选择偏好：</p>
        <ABPreferenceSelector
          disabled={disabled}
          onChange={onPreferenceChange}
          value={preference}
        />
      </div>

      {/* 审核意见 */}
      <div>
        <label className="block text-sm font-medium" htmlFor="ab-opinion">
          审核意见
          <textarea
            className="mt-1.5 w-full rounded border border-[var(--border)] bg-[var(--surface)] p-2 text-sm"
            disabled={disabled}
            id="ab-opinion"
            onChange={(e) => onOpinionChange(e.target.value)}
            placeholder="可选：添加审核意见"
            rows={3}
            value={opinion}
          />
        </label>
      </div>
    </div>
  );
}
