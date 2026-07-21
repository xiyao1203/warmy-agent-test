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
              <Badge>{executionModeLabel(caseItem.execution_mode)}</Badge>
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
            <Field label="用例编号" value={caseItem.case_key ?? "未编号"} />
            <Field label="状态" value={caseItem.case_status} />
            <Field label="类型" value={caseItem.case_type} />
            <Field label="自动化" value={caseItem.automation_status} />
            <Field label="来源" value={caseItem.source} />
            {caseItem.component && (
              <Field label="组件" value={caseItem.component} />
            )}
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

          <Section icon={<Target className="size-4" />} title="测试目标">
            <p className="whitespace-pre-wrap text-sm leading-6">
              {caseItem.objective}
            </p>
          </Section>

          {caseItem.preconditions.length > 0 && (
            <Section icon={<Settings className="size-4" />} title="前置条件">
              <OrderedText values={caseItem.preconditions} />
            </Section>
          )}

          {/* 输入数据 */}
          <Section icon={<Target className="size-4" />} title="输入数据">
            <JsonBlock data={caseItem.input} />
          </Section>

          {caseItem.data_bindings.length > 0 && (
            <Section icon={<Settings className="size-4" />} title="数据绑定">
              <JsonBlock data={caseItem.data_bindings} />
            </Section>
          )}

          {caseItem.steps.length > 0 && (
            <Section icon={<Layers className="size-4" />} title="标准操作步骤">
              <div className="space-y-3">
                {caseItem.steps.map((step, index) => (
                  <div
                    className="rounded border border-[var(--hairline)] p-3"
                    key={index}
                  >
                    <p className="text-xs font-semibold">
                      步骤 {Number(step.step_no ?? index + 1)}
                    </p>
                    <p className="mt-2 text-sm">{String(step.action ?? "")}</p>
                    {Boolean(step.test_data) ? (
                      <JsonBlock data={step.test_data} />
                    ) : null}
                    <p className="mt-2 text-xs text-[var(--muted)]">预期结果</p>
                    <p className="mt-1 text-sm">
                      {String(step.expected_result ?? "")}
                    </p>
                  </div>
                ))}
              </div>
            </Section>
          )}

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

          {caseItem.postconditions.length > 0 && (
            <Section icon={<Settings className="size-4" />} title="后置条件">
              <OrderedText values={caseItem.postconditions} />
            </Section>
          )}

          <Section icon={<Settings className="size-4" />} title="执行设置">
            <Field
              label="执行模式"
              value={executionModeLabel(caseItem.execution_mode)}
            />
            <Field
              label="预计时长"
              value={
                caseItem.estimated_duration_seconds
                  ? `${caseItem.estimated_duration_seconds} 秒`
                  : "未设置"
              }
            />
            <Field
              label="超时"
              value={
                caseItem.timeout_seconds
                  ? `${caseItem.timeout_seconds} 秒`
                  : "继承计划"
              }
            />
            <Field label="重试" value={`${caseItem.retry_count} 次`} />
          </Section>
        </div>
      </div>
    </div>
  );
}

function executionModeLabel(mode: string) {
  if (mode === "api") return "API";
  if (mode === "codex_explore") return "Codex 浏览器探索";
  return "浏览器";
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
    <pre className="text-code max-h-48 overflow-auto rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function OrderedText({ values }: { values: string[] }) {
  return (
    <ol className="list-decimal space-y-1 pl-5 text-sm">
      {values.map((value, index) => (
        <li key={`${value}-${index}`}>{value}</li>
      ))}
    </ol>
  );
}
