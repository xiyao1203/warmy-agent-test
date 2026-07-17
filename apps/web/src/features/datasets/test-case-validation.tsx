import type { TestCaseValidationResponse } from "@warmy/generated-api-client";

import { Badge } from "@/components/ui/badge";

export function TestCaseValidation({
  error,
  result,
}: {
  error?: string;
  result?: TestCaseValidationResponse;
}) {
  if (!error && !result) return null;
  return (
    <div
      aria-live="polite"
      className="rounded-[var(--radius-md)] border border-[var(--hairline)] p-3 text-sm"
      role={
        error || result?.issues.some((item) => item.severity === "error")
          ? "alert"
          : "status"
      }
    >
      {error ? (
        <p className="text-[var(--danger)]">{error}</p>
      ) : (
        <>
          <div className="flex items-center gap-2">
            <span className="font-medium">专业用例校验</span>
            <Badge tone={result?.ready ? "accent" : "danger"}>
              {result?.ready ? "可以标记就绪" : "需要修正"}
            </Badge>
          </div>
          {result?.issues.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs">
              {result.issues.map((issue, index) => (
                <li key={`${issue.field}-${issue.code}-${index}`}>
                  {issue.field}：{issue.message}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-xs text-[var(--muted)]">
              所有必填字段均符合平台标准。
            </p>
          )}
        </>
      )}
    </div>
  );
}
