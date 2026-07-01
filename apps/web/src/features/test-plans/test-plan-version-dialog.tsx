"use client";

import type {
  CreateTestPlanVersionRequest,
  TestPlanVersionResponse,
} from "@warmy/generated-api-client";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export type VersionAssetOption = {
  id: string;
  label: string;
  status?: "draft" | "published";
};

export function TestPlanVersionDialog({
  agentVersions,
  datasetVersions,
  environments,
  gates,
  runs,
  scorers,
  onSubmit,
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
  triggerLabel: string;
  version?: TestPlanVersionResponse;
}) {
  const config = version?.config ?? {};
  const [open, setOpen] = useState(false);
  const [agentVersionId, setAgentVersionId] = useState(
    version?.agent_version_id ?? "",
  );
  const [datasetVersionId, setDatasetVersionId] = useState(
    version?.dataset_version_id ?? "",
  );
  const [environmentId, setEnvironmentId] = useState(
    version?.environment_template_id ?? "",
  );
  const [concurrency, setConcurrency] = useState(
    Number(config.concurrency ?? 1),
  );
  const [timeout, setTimeout] = useState(Number(config.timeout ?? 300));
  const [runsPerCase, setRunsPerCase] = useState(
    Number(config.runs_per_case ?? 1),
  );
  const [passThreshold, setPassThreshold] = useState(
    Number(config.pass_threshold ?? 1),
  );
  const [maxRetries, setMaxRetries] = useState(Number(config.max_retries ?? 0));
  const [baselineRunId, setBaselineRunId] = useState(
    String(config.baseline_run_id ?? ""),
  );
  const [releaseGateId, setReleaseGateId] = useState(
    String(config.release_gate_id ?? ""),
  );
  const [scorerIds, setScorerIds] = useState<string[]>(
    Array.isArray(config.scorer_ids) ? config.scorer_ids.map(String) : [],
  );
  const [observationOnly, setObservationOnly] = useState(
    Boolean(config.observation_only ?? false),
  );
  const [error, setError] = useState("");
  const publishedAgents = agentVersions.filter(
    (option) => option.status === "published",
  );
  const publishedDatasets = datasetVersions.filter(
    (option) => option.status === "published",
  );

  async function submit() {
    try {
      await onSubmit({
        agent_version_id: agentVersionId || null,
        config: {
          baseline_run_id: baselineRunId || null,
          concurrency,
          max_retries: maxRetries,
          pass_threshold: passThreshold,
          release_gate_id: releaseGateId || null,
          scorer_ids: scorerIds,
          observation_only: observationOnly,
          runs_per_case: runsPerCase,
          timeout,
        },
        dataset_version_id: datasetVersionId || null,
        environment_template_id: environmentId || null,
      });
      setOpen(false);
      setError("");
    } catch {
      setError("保存版本失败，请检查配置和资产引用。");
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant={version ? "secondary" : "primary"}>
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogTitle>{version ? "编辑计划版本" : "创建计划版本"}</DialogTitle>
        <DialogDescription>
          选择已发布测试资产，并设置执行并发、超时和门禁阈值。
        </DialogDescription>
        <div className="mt-5 grid grid-cols-2 gap-4">
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
          <SelectField
            label="环境模板"
            onChange={setEnvironmentId}
            options={environments}
            value={environmentId}
          />
          <NumberField
            label="并发数"
            min={1}
            onChange={setConcurrency}
            value={concurrency}
          />
          <NumberField
            label="超时（秒）"
            min={1}
            onChange={setTimeout}
            value={timeout}
          />
          <NumberField
            label="每条用例运行次数"
            min={1}
            onChange={setRunsPerCase}
            value={runsPerCase}
          />
          <NumberField
            label="通过阈值"
            max={1}
            min={0}
            onChange={setPassThreshold}
            step={0.01}
            value={passThreshold}
          />
          <NumberField
            label="最大重试次数"
            min={0}
            onChange={setMaxRetries}
            value={maxRetries}
          />
          <div className="col-span-2">
            <label className="block text-sm font-medium">
              基线运行（可选）
              <AssetSelect
                onChange={setBaselineRunId}
                options={runs}
                value={baselineRunId}
              />
            </label>
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium">
              发布门禁（可选）
              <AssetSelect
                onChange={setReleaseGateId}
                options={gates}
                value={releaseGateId}
              />
            </label>
          </div>
          <div className="col-span-2 rounded border border-[var(--border)] p-3">
            <p className="text-sm font-medium">评分器</p>
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
            <label className="mt-3 flex items-center gap-2 text-sm">
              <input
                checked={observationOnly}
                onChange={(event) => setObservationOnly(event.target.checked)}
                type="checkbox"
              />
              仅观察模式（不配置评分器时必须显式开启）
            </label>
          </div>
        </div>
        {error ? (
          <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>
        ) : null}
        <div className="mt-5 flex justify-end gap-2">
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={submit} variant="primary">
            保存版本
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AssetSelect({
  onChange,
  options,
  value,
}: {
  onChange: (value: string) => void;
  options: VersionAssetOption[];
  value: string;
}) {
  return (
    <select
      className="mt-1.5 h-9 w-full rounded border border-[var(--border)] bg-[var(--surface)] px-3"
      onChange={(event) => onChange(event.target.value)}
      value={value}
    >
      <option value="">未选择</option>
      {options.map((option) => (
        <option key={option.id} value={option.id}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function SelectField({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: VersionAssetOption[];
  value: string;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <select
        aria-label={label}
        className="mt-1.5 h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface)] px-3"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value="">未选择</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function NumberField({
  label,
  max,
  min,
  onChange,
  step,
  value,
}: {
  label: string;
  max?: number;
  min: number;
  onChange: (value: number) => void;
  step?: number;
  value: number;
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <Input
        className="mt-1.5"
        max={max}
        min={min}
        onChange={(event) => onChange(Number(event.target.value))}
        step={step}
        type="number"
        value={value}
      />
    </label>
  );
}
