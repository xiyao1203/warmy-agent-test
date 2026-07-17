"use client";

import type {
  CreateTestPlanVersionRequest,
  TestPlanVersionResponse,
} from "@warmy/generated-api-client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { listBrowserProfiles } from "@/features/browser-profiles";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  AssetSelectField,
  NumberField,
  SelectField,
} from "./test-plan-version-fields";

export type VersionAssetOption = {
  id: string;
  label: string;
  status?: "draft" | "published";
};

// ── 四步向导步骤定义 ──────────────────────────────────────────

type StepKey = "assets" | "execution" | "evaluation" | "gates";

const STEPS: { key: StepKey; label: string; description: string }[] = [
  {
    key: "assets",
    label: "选择测试资产",
    description: "关联已发布的 Agent、数据集和环境模板",
  },
  {
    key: "execution",
    label: "执行配置",
    description: "并发、超时、重试和运行次数",
  },
  {
    key: "evaluation",
    label: "评估设置",
    description: "评分器选择和通过阈值",
  },
  {
    key: "gates",
    label: "门禁配置",
    description: "安全扫描、审查和发布门禁",
  },
];

// ── 就绪状态（来自 GET readiness API） ──────────────────────────

type ReadinessState = {
  ready: boolean;
  blocking_issues: string[];
  status: string;
} | null;

// ── 步骤指示器子组件 ──────────────────────────────────────────

function StepIndicator({ currentIndex }: { currentIndex: number }) {
  return (
    <div className="mb-5 flex items-center justify-center gap-2">
      {STEPS.map((step, idx) => (
        <div className="flex items-center gap-2" key={step.key}>
          <div
            className={`flex size-7 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
              idx < currentIndex
                ? "bg-[var(--primary)] text-[var(--on-primary)]"
                : idx === currentIndex
                  ? "border-2 border-[var(--primary)] text-[var(--primary)]"
                  : "border border-[var(--hairline)] text-[var(--muted)]"
            }`}
          >
            {idx < currentIndex ? "\u2713" : idx + 1}
          </div>
          <span
            className={`text-xs ${
              idx === currentIndex
                ? "font-medium text-[var(--foreground)]"
                : "text-[var(--muted)]"
            }`}
          >
            {step.label}
          </span>
          {idx < STEPS.length - 1 ? (
            <div
              className={`mx-1 h-px w-6 ${
                idx < currentIndex
                  ? "bg-[var(--primary)]"
                  : "bg-[var(--hairline)]"
              }`}
            />
          ) : null}
        </div>
      ))}
    </div>
  );
}

// ── 主组件 ─────────────────────────────────────────────────────

export function TestPlanVersionDialog({
  agentVersions,
  datasetVersions,
  environments,
  gates,
  runs,
  scorers,
  onSubmit,
  planId,
  projectId,
  triggerLabel,
  version,
}: {
  agentVersions: VersionAssetOption[];
  datasetVersions: VersionAssetOption[];
  environments: VersionAssetOption[];
  gates: VersionAssetOption[];
  runs: VersionAssetOption[];
  scorers: VersionAssetOption[];
  onSubmit: (payload: CreateTestPlanVersionRequest) => Promise<unknown>;
  planId?: string;
  projectId?: string;
  triggerLabel: string;
  version?: TestPlanVersionResponse;
}) {
  const config = version?.config ?? {};
  const [open, setOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  // Step 1 — 核心资产
  const [agentVersionId, setAgentVersionId] = useState(
    version?.agent_version_id ?? "",
  );
  const [datasetVersionId, setDatasetVersionId] = useState(
    version?.dataset_version_id ?? "",
  );
  const [environmentId, setEnvironmentId] = useState(
    version?.environment_template_id ?? "",
  );

  // Step 2 — 执行策略
  const [concurrency, setConcurrency] = useState(
    Number(config.concurrency ?? 1),
  );
  const [timeout, setTimeout_] = useState(Number(config.timeout ?? 300));
  const [runsPerCase, setRunsPerCase] = useState(
    Number(config.runs_per_case ?? 1),
  );
  const [maxRetries, setMaxRetries] = useState(Number(config.max_retries ?? 0));
  const [browserProfileId, setBrowserProfileId] = useState(
    String(config.browser_profile_id ?? ""),
  );
  const [codexModelMode, setCodexModelMode] = useState<"default" | "custom">(
    config.codex_model || config.codex_model_provider ? "custom" : "default",
  );
  const [codexModelProvider, setCodexModelProvider] = useState(
    String(config.codex_model_provider ?? ""),
  );
  const [codexModel, setCodexModel] = useState(
    String(config.codex_model ?? ""),
  );

  // 浏览器实例列表
  const [browserProfileOptions, setBrowserProfileOptions] = useState<
    { id: string; label: string }[]
  >([]);

  useEffect(() => {
    if (!projectId || !open) return;
    listBrowserProfiles(projectId)
      .then((profiles) =>
        setBrowserProfileOptions(
          profiles.map((p) => ({ id: p.profile_id, label: p.name })),
        ),
      )
      .catch(() => setBrowserProfileOptions([]));
  }, [projectId, open]);

  // Step 3 — 评估配置
  const [passThreshold, setPassThreshold] = useState(
    Number(config.pass_threshold ?? 1),
  );
  const [scorerIds, setScorerIds] = useState<string[]>(
    Array.isArray(config.scorer_ids) ? config.scorer_ids.map(String) : [],
  );
  const [observationOnly, setObservationOnly] = useState(
    Boolean(config.observation_only ?? false),
  );

  // Step 4 — 门禁
  const [costBudget, setCostBudget] = useState(
    config.cost_budget != null ? String(config.cost_budget) : "",
  );
  const [baselineRunId, setBaselineRunId] = useState(
    String(config.baseline_run_id ?? ""),
  );
  const [releaseGateId, setReleaseGateId] = useState(
    String(config.release_gate_id ?? ""),
  );
  const [securityProfileIds] = useState<string[]>(
    Array.isArray(config.security_profile_ids)
      ? config.security_profile_ids.map(String)
      : [],
  );
  const [reviewPolicyId, setReviewPolicyId] = useState(
    String(config.review_policy_id ?? ""),
  );

  const [error, setError] = useState("");
  const [readiness, setReadiness] = useState<ReadinessState>(null);
  const [checkingReadiness, setCheckingReadiness] = useState(false);

  const publishedAgents = agentVersions.filter(
    (option) => option.status === "published",
  );
  const publishedDatasets = datasetVersions.filter(
    (option) => option.status === "published",
  );

  // ── 步骤导航 ───────────────────────────────────────────────
  function goToNext() {
    if (stepIndex < STEPS.length - 1) {
      setStepIndex((prev) => prev + 1);
    }
  }

  function goToPrev() {
    if (stepIndex > 0) {
      setStepIndex((prev) => prev - 1);
    }
  }

  async function checkReadiness() {
    if (!version?.id || !projectId || !planId) return;
    setCheckingReadiness(true);
    try {
      const mod = await import("@warmy/generated-api-client");
      const result =
        await mod.checkReadinessApiV1ProjectsProjectIdTestPlansPlanIdVersionsVersionIdReadinessGet(
          {
            path: {
              project_id: projectId,
              plan_id: planId,
              version_id: version.id,
            },
          },
        );
      if (result.data) {
        setReadiness(result.data as ReadinessState);
      }
    } catch {
      setReadiness(null);
    } finally {
      setCheckingReadiness(false);
    }
  }

  async function submit() {
    try {
      await onSubmit({
        agent_version_id: agentVersionId || null,
        config: {
          baseline_run_id: baselineRunId || null,
          concurrency,
          cost_budget: costBudget ? parseFloat(costBudget) : null,
          max_retries: maxRetries,
          observation_only: observationOnly,
          pass_threshold: passThreshold,
          release_gate_id: releaseGateId || null,
          review_policy_id: reviewPolicyId || null,
          scorer_ids: scorerIds,
          security_profile_ids: securityProfileIds,
          runs_per_case: runsPerCase,
          timeout,
          browser_profile_id: browserProfileId,
          codex_model: codexModelMode === "custom" ? codexModel.trim() : "",
          codex_model_provider:
            codexModelMode === "custom" ? codexModelProvider.trim() : "",
        },
        dataset_version_id: datasetVersionId || null,
        environment_template_id: environmentId || null,
      });
      setOpen(false);
      setError("");
      setStepIndex(0);
    } catch {
      setError("保存版本失败，请检查配置和资产引用。");
    }
  }

  function reset() {
    setStepIndex(0);
    setReadiness(null);
    setError("");
  }

  // ── Step 内容 ──────────────────────────────────────────────

  const stepDesc = STEPS[stepIndex].description;

  const currentStepContent = (
    <div className="mt-5 grid grid-cols-2 gap-4">
      {stepIndex === 0 ? (
        <>
          <SelectField
            label="Agent 版本"
            onChange={setAgentVersionId}
            options={publishedAgents}
            value={agentVersionId}
          />
          <SelectField
            label="数据集版本"
            onChange={setDatasetVersionId}
            options={publishedDatasets}
            value={datasetVersionId}
          />
          <div className="col-span-2">
            <SelectField
              label="环境模板"
              onChange={setEnvironmentId}
              options={environments}
              value={environmentId}
            />
            <p className="mt-1.5 text-xs text-[var(--muted)]">
              环境来自“环境与凭证”页面；发布环境版本后，计划执行时会自动注入已绑定凭证。
              {projectId ? (
                <Link
                  className="ml-1 font-medium text-[var(--primary)] hover:underline"
                  href={`/projects/${projectId}/environments`}
                >
                  去管理环境
                </Link>
              ) : null}
            </p>
          </div>
        </>
      ) : stepIndex === 1 ? (
        <>
          <NumberField
            label="并发数"
            min={1}
            onChange={setConcurrency}
            value={concurrency}
          />
          <NumberField
            label="超时（秒）"
            min={1}
            onChange={setTimeout_}
            value={timeout}
          />
          <NumberField
            label="每条用例运行次数"
            min={1}
            onChange={setRunsPerCase}
            value={runsPerCase}
          />
          <NumberField
            label="最大重试次数"
            min={0}
            onChange={setMaxRetries}
            value={maxRetries}
          />
          <SelectField
            label="浏览器实例"
            onChange={setBrowserProfileId}
            options={browserProfileOptions}
            value={browserProfileId}
          />
          <SelectField
            label="Codex 执行模型"
            onChange={(value) =>
              setCodexModelMode(value === "custom" ? "custom" : "default")
            }
            options={[{ id: "custom", label: "手动指定其他模型" }]}
            placeholder="使用 Codex CLI 默认配置"
            value={codexModelMode === "custom" ? "custom" : ""}
          />
          <p className="col-span-2 -mt-2 text-xs text-[var(--muted)]">
            浏览器实例来自“浏览器实例”页面；浏览器用例运行时会复用选中实例的登录态和用户目录。
            {projectId ? (
              <Link
                className="ml-1 font-medium text-[var(--primary)] hover:underline"
                href={`/projects/${projectId}/browser-profiles`}
              >
                去管理浏览器实例
              </Link>
            ) : null}
          </p>
          {codexModelMode === "custom" ? (
            <>
              <label className="block text-sm font-medium">
                Codex Provider ID
                <Input
                  className="mt-1.5"
                  onChange={(event) =>
                    setCodexModelProvider(event.target.value)
                  }
                  placeholder="例如 openai、ollama 或公司内配置名"
                  value={codexModelProvider}
                />
              </label>
              <label className="block text-sm font-medium">
                Codex 模型 ID
                <Input
                  className="mt-1.5"
                  onChange={(event) => setCodexModel(event.target.value)}
                  placeholder="例如 gpt-5.5、gpt-oss-120b"
                  value={codexModel}
                />
              </label>
              <p className="col-span-2 -mt-2 text-xs leading-5 text-[var(--muted)]">
                这里不会读取平台模型 API Key；请填写运行机器 Codex CLI
                已配置好的供应商和模型。留空时继续使用 Codex CLI
                默认配置，Chrome 实例只负责登录态和浏览器目录。
              </p>
            </>
          ) : (
            <p className="col-span-2 -mt-2 text-xs leading-5 text-[var(--muted)]">
              默认使用运行机器上的 Codex CLI 模型配置；Chrome
              实例只负责登录态和浏览器目录，不绑定 OpenAI。
            </p>
          )}
        </>
      ) : stepIndex === 2 ? (
        <>
          <div className="col-span-2 rounded border border-[var(--hairline)] p-3">
            <p className="text-sm font-medium">评分器</p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              评分器来自“评分器”页面；运行完成后会生成评分结果，并可用于实验对比和发布门禁。
              {projectId ? (
                <>
                  <Link
                    className="ml-1 font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/scorers`}
                  >
                    去管理评分器
                  </Link>
                  <Link
                    className="ml-2 font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/experiments`}
                  >
                    去实验对比
                  </Link>
                </>
              ) : null}
            </p>
            {scorers.length === 0 ? (
              <p className="mt-1 text-xs text-[var(--muted)]">暂无可用评分器</p>
            ) : (
              <div className="mt-2 flex flex-wrap gap-3">
                {scorers.map((scorer) => (
                  <label
                    className="flex items-center gap-2 text-sm"
                    key={scorer.id}
                  >
                    <input
                      checked={scorerIds.includes(scorer.id)}
                      onChange={(event) =>
                        setScorerIds((current) =>
                          event.target.checked
                            ? [...current, scorer.id]
                            : current.filter((id) => id !== scorer.id),
                        )
                      }
                      type="checkbox"
                    />
                    {scorer.label}
                  </label>
                ))}
              </div>
            )}
            <label className="mt-3 flex items-center gap-2 text-sm">
              <input
                checked={observationOnly}
                onChange={(event) => setObservationOnly(event.target.checked)}
                type="checkbox"
              />
              仅观察模式（不配置评分器时必须显式开启）
            </label>
          </div>
          <NumberField
            label="通过阈值"
            max={1}
            min={0}
            onChange={setPassThreshold}
            step={0.01}
            value={passThreshold}
          />
          <div />
        </>
      ) : (
        <>
          <div className="col-span-2 rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-3">
            <p className="text-sm font-medium">发布前检查</p>
            <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
              门禁会读取测试执行的通过率、同一次运行的安全评分和待人工审核数量；实验对比用于发现版本退化，再决定是否放行。
              {projectId ? (
                <>
                  <Link
                    className="ml-1 font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/security`}
                  >
                    去安全测试
                  </Link>
                  <Link
                    className="ml-2 font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/reviews`}
                  >
                    去人工审核
                  </Link>
                  <Link
                    className="ml-2 font-medium text-[var(--primary)] hover:underline"
                    href={`/projects/${projectId}/gates`}
                  >
                    去发布门禁
                  </Link>
                </>
              ) : null}
            </p>
          </div>
          <NumberField
            label="费用预算（可选）"
            min={0}
            onChange={(value) => setCostBudget(String(value))}
            step={0.01}
            value={costBudget ? parseFloat(costBudget) : 0}
          />
          <AssetSelectField
            label="审查策略（可选）"
            onChange={setReviewPolicyId}
            options={[]}
            value={reviewPolicyId}
          />
          <div className="col-span-2">
            <p className="mb-1 text-xs text-[var(--muted)]">
              审查策略暂由管理员配置；安全测试可在“安全测试”页面直接启动。
            </p>
            <AssetSelectField
              label="基线运行（可选）"
              onChange={setBaselineRunId}
              options={runs}
              value={baselineRunId}
            />
          </div>
          <div className="col-span-2">
            <AssetSelectField
              label="发布门禁（可选）"
              onChange={setReleaseGateId}
              options={gates}
              value={releaseGateId}
            />
          </div>

          {/* ── 就绪检查（仅编辑已有版本时显示）── */}
          {version?.id ? (
            <div className="col-span-2 rounded border border-[var(--hairline)] p-3">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium">资产就绪检查</p>
                {checkingReadiness ? (
                  <span className="text-xs text-[var(--muted)]">检查中...</span>
                ) : readiness ? (
                  readiness.ready ? (
                    <span className="rounded bg-[var(--success-subtle)] px-2 py-0.5 text-xs font-medium text-[var(--success)]">
                      就绪
                    </span>
                  ) : (
                    <span className="rounded bg-[var(--warning-subtle)] px-2 py-0.5 text-xs font-medium text-[var(--warning)]">
                      待完善
                    </span>
                  )
                ) : (
                  <Button
                    className="h-6 px-2 text-xs"
                    onClick={checkReadiness}
                    variant="secondary"
                  >
                    检查
                  </Button>
                )}
              </div>
              {readiness && readiness.blocking_issues.length > 0 ? (
                <ul className="mt-2 list-inside list-disc space-y-0.5 text-xs text-[var(--muted)]">
                  {readiness.blocking_issues.map((issue) => (
                    <li key={issue}>{issue}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );

  return (
    <Dialog
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (!isOpen) reset();
      }}
      open={open}
    >
      <DialogTrigger asChild>
        <Button variant={version ? "secondary" : "primary"}>
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogTitle>{version ? "编辑计划版本" : "创建计划版本"}</DialogTitle>
        <DialogDescription>{stepDesc}</DialogDescription>

        {/* 步骤指示器 */}
        <StepIndicator currentIndex={stepIndex} />

        {/* 步骤内容 */}
        {currentStepContent}

        {error ? (
          <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>
        ) : null}

        {/* 步骤导航按钮 */}
        <div className="mt-5 flex justify-between gap-2">
          <div className="flex gap-2">
            {stepIndex > 0 ? (
              <Button onClick={goToPrev} variant="secondary">
                上一步
              </Button>
            ) : (
              <Button onClick={() => setOpen(false)} variant="secondary">
                取消
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {stepIndex < STEPS.length - 1 ? (
              <Button onClick={goToNext} variant="primary">
                下一步
              </Button>
            ) : (
              <Button
                disabled={readiness != null && !readiness.ready}
                onClick={submit}
                variant="primary"
              >
                保存版本
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
