"use client";

import type { TestCaseResponse } from "@warmy/generated-api-client";
import { Layers, Target, Shield, Tag, Settings } from "lucide-react";

import { Badge } from "@/components/ui/badge";

type TestCaseDetailProps = {
  caseItem: TestCaseResponse;
  open: boolean;
  onClose: () => void;
};

export function TestCaseDetail({
  caseItem,
  open,
  onClose,
}: TestCaseDetailProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* 遮罩 */}
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
        role="button"
        tabIndex={0}
        aria-label="关闭"
      />

      {/* 抽屉内容 */}
      <div className="relative z-10 w-full max-w-lg overflow-y-auto border-l border-[var(--hairline)] bg-[var(--surface)] p-6">
        {/* 头部 */}
        <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-4">
          <div>
            <h2 className="text-lg font-semibold">{caseItem.name}</h2>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge>
                {caseItem.execution_mode === "api" ? "API" : "浏览器"}
              </Badge>
              {caseItem.priority && <Badge>{caseItem.priority}</Badge>}
              {caseItem.risk_level && <Badge>{caseItem.risk_level}</Badge>}
              {caseItem.difficulty && <Badge>{caseItem.difficulty}</Badge>}
              {caseItem.test_group && <Badge>{caseItem.test_group}</Badge>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-[var(--canvas-soft)]"
            aria-label="关闭"
          >
            <svg className="size-5" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        {/* 内容 */}
        <div className="mt-6 space-y-6">
          {/* 基本信息 */}
          <Section icon={<Layers className="size-4" />} title="基本信息">
            <Field label="ID" value={caseItem.id} />
            {caseItem.scenario && (
              <Field label="业务场景" value={caseItem.scenario} />
            )}
            {caseItem.tags && caseItem.tags.length > 0 && (
              <div>
                <span className="text-sm text-[var(--muted)]">标签</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {caseItem.tags.map((tag, i) => (
                    <Badge key={i}>{tag}</Badge>
                  ))}
                </div>
              </div>
            )}
          </Section>

          {/* 输入数据 */}
          <Section icon={<Target className="size-4" />} title="输入数据">
            <JsonBlock data={caseItem.input} />
          </Section>

          {/* 初始状态 */}
          {caseItem.initial_state &&
            Object.keys(caseItem.initial_state).length > 0 && (
              <Section
                icon={<Settings className="size-4" />}
                title="初始业务状态"
              >
                <JsonBlock data={caseItem.initial_state} />
              </Section>
            )}

          {/* 预期输出 */}
          {caseItem.expected_outcome &&
            Object.keys(caseItem.expected_outcome).length > 0 && (
              <Section icon={<Target className="size-4" />} title="预期输出">
                <JsonBlock data={caseItem.expected_outcome} />
              </Section>
            )}

          <Section icon={<Shield className="size-4" />} title="断言规则">
            {caseItem.assertions && caseItem.assertions.length > 0 ? (
              <JsonBlock data={caseItem.assertions} />
            ) : (
              <p className="rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3 text-sm text-[var(--muted)]">
                未配置断言
              </p>
            )}
          </Section>

          {/* 评分器 */}
          {caseItem.scorers && caseItem.scorers.length > 0 && (
            <Section icon={<Tag className="size-4" />} title="评分器配置">
              <JsonBlock data={caseItem.scorers} />
            </Section>
          )}

          {/* 安全策略 */}
          {caseItem.security_policies &&
            caseItem.security_policies.length > 0 && (
              <Section icon={<Shield className="size-4" />} title="安全策略">
                <JsonBlock data={caseItem.security_policies} />
              </Section>
            )}
        </div>
      </div>
    </div>
  );
}

/* ── 子组件 ────────────────────────────────────────────────────────── */

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--ink)]">
        {icon}
        {title}
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-[var(--muted)]">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre className="max-h-48 overflow-auto rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3 text-xs font-mono">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
