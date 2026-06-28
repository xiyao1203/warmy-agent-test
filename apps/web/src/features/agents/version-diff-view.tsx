"use client";

import { useState } from "react";
import { ArrowLeftRight, Check, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type DiffField = {
  field: string;
  left_value: unknown;
  right_value: unknown;
  changed: boolean;
};

export type VersionDiffResponse = {
  v1: {
    id: string;
    version_number: number;
    status: string;
  };
  v2: {
    id: string;
    version_number: number;
    status: string;
  };
  fields: DiffField[];
};

type VersionDiffViewProps = {
  v1Id: string;
  v2Id: string;
  v1Number?: number;
  v2Number?: number;
  onFetchDiff: (v1Id: string, v2Id: string) => Promise<VersionDiffResponse>;
};

export function VersionDiffView({
  v1Id,
  v2Id,
  v1Number,
  v2Number,
  onFetchDiff,
}: VersionDiffViewProps) {
  const [diff, setDiff] = useState<VersionDiffResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showOnlyChanges, setShowOnlyChanges] = useState(false);

  async function handleFetch() {
    setLoading(true);
    setError(null);
    try {
      const result = await onFetchDiff(v1Id, v2Id);
      setDiff(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "获取对比结果失败");
    } finally {
      setLoading(false);
    }
  }

  const fields = diff?.fields ?? [];
  const filteredFields = showOnlyChanges ? fields.filter((f) => f.changed) : fields;
  const changedCount = fields.filter((f) => f.changed).length;

  return (
    <div className="space-y-4">
      {/* 操作栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ArrowLeftRight className="size-4 text-[var(--text-muted)]" />
          <span className="text-sm font-medium">
            版本对比：v{v1Number ?? "?"} vs v{v2Number ?? "?"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {diff && (
            <>
              <label className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                <input
                  checked={showOnlyChanges}
                  onChange={(e) => setShowOnlyChanges(e.target.checked)}
                  type="checkbox"
                  className="rounded"
                />
                仅显示变更
              </label>
              <Badge tone={changedCount > 0 ? "warning" : "success"}>
                {changedCount} 项变更
              </Badge>
            </>
          )}
          <Button disabled={loading} onClick={handleFetch} variant="primary">
            {loading ? "加载中..." : diff ? "刷新" : "开始对比"}
          </Button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="rounded border border-[var(--error)] bg-[var(--error-subtle)] p-3 text-sm text-[var(--error)]">
          {error}
        </div>
      )}

      {/* 对比结果 */}
      {diff && (
        <div className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border)]">
          {/* 表头 */}
          <div className="grid grid-cols-[200px_1fr_1fr_60px] border-b border-[var(--border)] bg-[var(--surface-subtle)] text-xs font-medium text-[var(--text-muted)]">
            <div className="px-4 py-2">字段</div>
            <div className="border-l border-[var(--border)] px-4 py-2">
              v{diff.v1.version_number}（{diff.v1.status === "published" ? "已发布" : "草稿"}）
            </div>
            <div className="border-l border-[var(--border)] px-4 py-2">
              v{diff.v2.version_number}（{diff.v2.status === "published" ? "已发布" : "草稿"}）
            </div>
            <div className="border-l border-[var(--border)] px-4 py-2 text-center">变更</div>
          </div>

          {/* 字段行 */}
          {filteredFields.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">
              {showOnlyChanges ? "没有变更的字段" : "没有可对比的字段"}
            </div>
          ) : (
            filteredFields.map((field) => (
              <DiffRow key={field.field} field={field} />
            ))
          )}
        </div>
      )}

      {/* 空状态 */}
      {!diff && !loading && !error && (
        <div className="rounded-[var(--radius-md)] border border-[var(--border)] p-8 text-center">
          <ArrowLeftRight className="mx-auto size-8 text-[var(--text-muted)]" />
          <p className="mt-3 text-sm font-medium">点击「开始对比」查看两个版本的差异</p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            对比 API 地址、模型、参数、工具、Prompt 等所有配置字段
          </p>
        </div>
      )}
    </div>
  );
}

/* ── Diff 行 ────────────────────────────────────────────────────────── */

function DiffRow({ field }: { field: DiffField }) {
  const leftStr = formatValue(field.left_value);
  const rightStr = formatValue(field.right_value);

  return (
    <div
      className={`grid grid-cols-[200px_1fr_1fr_60px] border-b border-[var(--border)] last:border-b-0 ${
        field.changed ? "bg-[var(--warning-subtle)]" : ""
      }`}
    >
      {/* 字段名 */}
      <div className="px-4 py-2 text-xs font-medium text-[var(--text)]">
        {field.field}
      </div>

      {/* 左侧值 */}
      <div className="border-l border-[var(--border)] px-4 py-2 text-xs">
        <ValueDisplay value={leftStr} changed={field.changed} side="left" />
      </div>

      {/* 右侧值 */}
      <div className="border-l border-[var(--border)] px-4 py-2 text-xs">
        <ValueDisplay value={rightStr} changed={field.changed} side="right" />
      </div>

      {/* 变更标记 */}
      <div className="flex items-center justify-center border-l border-[var(--border)]">
        {field.changed ? (
          <Check className="size-4 text-[var(--warning)]" />
        ) : (
          <X className="size-4 text-[var(--text-muted)]" />
        )}
      </div>
    </div>
  );
}

function ValueDisplay({
  value,
  changed,
  side,
}: {
  value: string;
  changed: boolean;
  side: "left" | "right";
}) {
  if (!changed) {
    return <span className="text-[var(--text-muted)]">{value}</span>;
  }

  return (
    <span
      className={`font-medium ${
        side === "left" ? "text-[var(--error)] line-through" : "text-[var(--success)]"
      }`}
    >
      {value}
    </span>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
