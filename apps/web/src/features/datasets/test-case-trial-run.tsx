"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { DropdownSelect } from "@/components/ui/dropdown-select";

export type TrialRunTarget = { id: string; name: string };

export function TestCaseTrialRun({
  agents,
  environments,
  onRun,
}: {
  agents: TrialRunTarget[];
  environments: TrialRunTarget[];
  onRun: (
    agentVersionId: string,
    environmentTemplateId: string,
  ) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [agentVersionId, setAgentVersionId] = useState("");
  const [environmentId, setEnvironmentId] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    if (!agentVersionId || !environmentId || !confirmed) return;
    setSubmitting(true);
    setError("");
    try {
      await onRun(agentVersionId, environmentId);
      setOpen(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "试运行创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button aria-label="AI 试运行" variant="secondary">
          AI 试运行
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>发起单用例 AI 试运行</DialogTitle>
        <DialogDescription>
          平台会固化当前专业用例快照，并交给已发布 Agent 版本执行。
        </DialogDescription>
        <div className="mt-4 space-y-4">
          <label className="block text-sm font-medium">
            Agent 版本
            <DropdownSelect
              aria-label="试运行 Agent 版本"
              className="mt-1.5 w-full"
              onChange={(event) => setAgentVersionId(event.target.value)}
              value={agentVersionId}
            >
              <option value="">请选择已发布 Agent 版本</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </DropdownSelect>
          </label>
          <label className="block text-sm font-medium">
            执行环境
            <DropdownSelect
              aria-label="试运行执行环境"
              className="mt-1.5 w-full"
              onChange={(event) => setEnvironmentId(event.target.value)}
              value={environmentId}
            >
              <option value="">请选择环境</option>
              {environments.map((environment) => (
                <option key={environment.id} value={environment.id}>
                  {environment.name}
                </option>
              ))}
            </DropdownSelect>
          </label>
          <label className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--warning)] p-3 text-sm">
            <input
              checked={confirmed}
              className="mt-0.5"
              onChange={(event) => setConfirmed(event.target.checked)}
              type="checkbox"
            />
            我确认该用例可能调用外部目标或产生测试数据，并同意按当前安全边界执行。
          </label>
          {(!agents.length || !environments.length) && (
            <p className="text-xs text-[var(--muted)]">
              需要先发布至少一个 Agent 版本并创建执行环境。
            </p>
          )}
          {error && (
            <p className="text-sm text-[var(--danger)]" role="alert">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button
              disabled={!agentVersionId || !environmentId || !confirmed}
              loading={submitting}
              onClick={() => void run()}
              variant="primary"
            >
              确认并开始
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
