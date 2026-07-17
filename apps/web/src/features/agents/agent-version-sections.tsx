import type { InvocationProtocol } from "@warmy/generated-api-client";

import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";

import { PROTOCOL_LABELS } from "./agent-version-form";

export function LimitsSection({
  blockedActions,
  costLimit,
  maxSteps,
  onBlockedActionsChange,
  onCostLimitChange,
  onMaxStepsChange,
  onRequiresConfirmationChange,
  onTimeoutChange,
  requiresConfirmation,
  timeout,
}: {
  blockedActions: string[];
  costLimit: string;
  maxSteps: string;
  onBlockedActionsChange: (value: string[]) => void;
  onCostLimitChange: (value: string) => void;
  onMaxStepsChange: (value: string) => void;
  onRequiresConfirmationChange: (value: boolean) => void;
  onTimeoutChange: (value: number) => void;
  requiresConfirmation: boolean;
  timeout: number;
}) {
  function toggleAction(action: string) {
    onBlockedActionsChange(
      blockedActions.includes(action)
        ? blockedActions.filter((item) => item !== action)
        : [...blockedActions, action],
    );
  }
  return (
    <>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="block text-sm font-medium">
          超时（秒，1–600）
          <Input
            className="mt-1.5"
            max={600}
            min={1}
            onChange={(event) => onTimeoutChange(Number(event.target.value))}
            type="number"
            value={timeout}
          />
        </label>
        <label className="block text-sm font-medium">
          最大步数
          <Input
            className="mt-1.5"
            min={1}
            onChange={(event) => onMaxStepsChange(event.target.value)}
            type="number"
            value={maxSteps}
          />
        </label>
        <label className="block text-sm font-medium">
          成本上限（USD）
          <Input
            className="mt-1.5"
            min={0}
            onChange={(event) => onCostLimitChange(event.target.value)}
            placeholder="不限制"
            step="0.01"
            type="number"
            value={costLimit}
          />
        </label>
      </div>
      <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] p-4">
        <p className="text-sm font-medium">只读安全边界</p>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {[
            ["delete", "禁止删除"],
            ["payment", "禁止支付/订阅"],
            ["publish", "禁止发布"],
            ["permission_change", "禁止权限变更"],
          ].map(([value, label]) => (
            <label className="flex items-center gap-2 text-sm" key={value}>
              <input
                checked={blockedActions.includes(value)}
                onChange={() => toggleAction(value)}
                type="checkbox"
              />
              {label}
            </label>
          ))}
        </div>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input
            checked={requiresConfirmation}
            onChange={(event) =>
              onRequiresConfirmationChange(event.target.checked)
            }
            type="checkbox"
          />
          高风险操作必须停下等待人工确认
        </label>
      </div>
    </>
  );
}

export function MetadataSection({
  adapterId,
  adapterVersion,
  codeVersion,
  credentialIds,
  gitCommit,
  knowledgeVersion,
  model,
  modelParams,
  onAdapterIdChange,
  onAdapterVersionChange,
  onCodeVersionChange,
  onCredentialIdsChange,
  onGitCommitChange,
  onKnowledgeVersionChange,
  onModelChange,
  onModelParamsChange,
  onProtocolChange,
  onSystemPromptChange,
  onSystemPromptVersionChange,
  onToolsChange,
  protocol,
  systemPrompt,
  systemPromptVersion,
  tools,
}: {
  adapterId: string;
  adapterVersion: string;
  codeVersion: string;
  credentialIds: string;
  gitCommit: string;
  isEditing: boolean;
  knowledgeVersion: string;
  model: string;
  modelParams: string;
  onAdapterIdChange: (value: string) => void;
  onAdapterVersionChange: (value: string) => void;
  onCodeVersionChange: (value: string) => void;
  onCredentialIdsChange: (value: string) => void;
  onGitCommitChange: (value: string) => void;
  onKnowledgeVersionChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onModelParamsChange: (value: string) => void;
  onProtocolChange: (value: InvocationProtocol) => void;
  onSystemPromptChange: (value: string) => void;
  onSystemPromptVersionChange: (value: string) => void;
  onToolsChange: (value: string) => void;
  protocol: InvocationProtocol;
  systemPrompt: string;
  systemPromptVersion: string;
  tools: string;
}) {
  return (
    <>
      <label className="block text-sm font-medium">
        调用协议
        <DropdownSelect
          className="mt-1.5 h-9 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] px-3"
          onChange={(event) =>
            onProtocolChange(event.target.value as InvocationProtocol)
          }
          value={protocol}
        >
          {(
            Object.entries(PROTOCOL_LABELS) as [InvocationProtocol, string][]
          ).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </DropdownSelect>
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-sm font-medium">
          模型
          <Input
            className="mt-1.5"
            onChange={(event) => onModelChange(event.target.value)}
            placeholder="例如 gpt-4o（仅 Trace 记录）"
            value={model}
          />
        </label>
        <label className="block text-sm font-medium">
          Prompt 版本
          <Input
            className="mt-1.5"
            onChange={(event) =>
              onSystemPromptVersionChange(event.target.value)
            }
            value={systemPromptVersion}
          />
        </label>
        <label className="block text-sm font-medium">
          代码版本
          <Input
            className="mt-1.5"
            onChange={(event) => onCodeVersionChange(event.target.value)}
            placeholder="v1.2.0"
            value={codeVersion}
          />
        </label>
        <label className="block text-sm font-medium">
          Git Commit
          <Input
            className="mt-1.5"
            onChange={(event) => onGitCommitChange(event.target.value)}
            placeholder="abc1234"
            value={gitCommit}
          />
        </label>
        <label className="block text-sm font-medium">
          Adapter ID
          <Input
            className="mt-1.5"
            onChange={(event) => onAdapterIdChange(event.target.value)}
            value={adapterId}
          />
        </label>
        <label className="block text-sm font-medium">
          Adapter 版本
          <Input
            className="mt-1.5"
            onChange={(event) => onAdapterVersionChange(event.target.value)}
            value={adapterVersion}
          />
        </label>
        <label className="block text-sm font-medium">
          知识库版本
          <Input
            className="mt-1.5"
            onChange={(event) => onKnowledgeVersionChange(event.target.value)}
            value={knowledgeVersion}
          />
        </label>
        <label className="block text-sm font-medium">
          其他凭证 ID（逗号分隔）
          <Input
            className="mt-1.5"
            onChange={(event) => onCredentialIdsChange(event.target.value)}
            value={credentialIds}
          />
        </label>
      </div>
      <label className="block text-sm font-medium">
        系统提示词
        <textarea
          className="mt-1.5 min-h-20 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] p-3 text-xs"
          onChange={(event) => onSystemPromptChange(event.target.value)}
          placeholder="仅 Trace 记录"
          value={systemPrompt}
        />
      </label>
      <label className="block text-sm font-medium">
        模型参数（JSON）
        <textarea
          className="mt-1.5 min-h-20 w-full rounded border border-[var(--hairline)] p-3 font-mono text-xs"
          onChange={(event) => onModelParamsChange(event.target.value)}
          value={modelParams}
        />
      </label>
      <label className="block text-sm font-medium">
        工具及 Schema（JSON 数组）
        <textarea
          className="mt-1.5 min-h-24 w-full rounded border border-[var(--hairline)] p-3 font-mono text-xs"
          onChange={(event) => onToolsChange(event.target.value)}
          value={tools}
        />
      </label>
    </>
  );
}
