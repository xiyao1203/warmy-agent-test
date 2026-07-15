"use client";

import type {
  AgentVersionResponse,
  CreateAgentVersionRequest,
  InvocationProtocol,
} from "@warmy/generated-api-client";
import { useEffect, useMemo, useState } from "react";

import {
  listBrowserProfiles,
  type BrowserProfile,
} from "@/features/browser-profiles";
import {
  createCredentialBinding,
  listCredentialBindings,
  type CredentialBinding,
} from "@/features/environments";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ConnectionTestPanel } from "./connection-test-panel";

type AgentVersionDialogProps = {
  triggerLabel: string;
  version?: AgentVersionResponse;
  projectId: string;
  agentId: string;
  onSubmit: (payload: CreateAgentVersionRequest) => Promise<void>;
};

type LoginStrategy =
  | "browser_profile"
  | "credential"
  | "none"
  | "username_password";
type TestScope = "guided" | "readonly";

type TargetPluginTemplate = {
  description: string;
  pluginId: string;
  targetType: "web_agent" | "api_agent";
  version: string;
};

const TARGET_PLUGIN_TEMPLATES: TargetPluginTemplate[] = [
  {
    description: "浏览器里可对话的目标 Agent，适合客服、SaaS、画布和后台系统。",
    pluginId: "generic-web-agent",
    targetType: "web_agent",
    version: "1.0.0",
  },
  {
    description: "TapNow 画布 Agent，默认使用画布地址和只读安全边界。",
    pluginId: "tapnow-canvas-agent",
    targetType: "web_agent",
    version: "1.0.0",
  },
  {
    description: "标准 HTTP/API Agent，适合已有接口和 OpenAI 兼容协议。",
    pluginId: "generic-http-agent",
    targetType: "api_agent",
    version: "1.0.0",
  },
];

const PROTOCOL_LABELS: Record<InvocationProtocol, string> = {
  async_poll: "异步轮询",
  openai_chat: "OpenAI Chat Compatible",
  sse: "SSE 流式",
  sync_json: "同步 JSON",
};

const DEFAULT_BLOCKED_ACTIONS = [
  "delete",
  "payment",
  "publish",
  "permission_change",
] as const;

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringValue(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function stringArray(value: unknown) {
  return Array.isArray(value) ? value.map(String) : [];
}

function numberValue(value: unknown, fallback: number) {
  return typeof value === "number" ? value : fallback;
}

function selectedTemplate(pluginId: string) {
  return (
    TARGET_PLUGIN_TEMPLATES.find(
      (template) => template.pluginId === pluginId,
    ) ?? TARGET_PLUGIN_TEMPLATES[0]
  );
}

export function AgentVersionDialog({
  agentId,
  onSubmit,
  projectId,
  triggerLabel,
  version,
}: AgentVersionDialogProps) {
  const config = version?.config ?? {};
  const targetConfig = asRecord(config.target_config);
  const loginConfig = asRecord(targetConfig.login);
  const selectorsConfig = asRecord(targetConfig.selectors);
  const safetyConfig = asRecord(targetConfig.safety_boundaries);

  const [open, setOpen] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const [targetPluginId, setTargetPluginId] = useState(
    stringValue(
      targetConfig.plugin_id,
      stringValue(config.plugin_id, "generic-web-agent"),
    ),
  );
  const targetPlugin = useMemo(
    () => selectedTemplate(targetPluginId),
    [targetPluginId],
  );

  const [targetUrl, setTargetUrl] = useState(
    stringValue(
      targetConfig.entry_url,
      stringValue(config.web_url, stringValue(config.api_url)),
    ),
  );
  const [apiUrl, setApiUrl] = useState(stringValue(config.api_url));
  const [protocol, setProtocol] = useState<InvocationProtocol>(
    (config.protocol as InvocationProtocol) ?? "sync_json",
  );
  const [loginStrategy, setLoginStrategy] = useState<LoginStrategy>(
    (loginConfig.strategy as LoginStrategy) ?? "none",
  );
  const [credentialId, setCredentialId] = useState(
    stringValue(loginConfig.credential_binding_id),
  );
  const [browserProfileId, setBrowserProfileId] = useState(
    stringValue(targetConfig.browser_profile_id),
  );
  const [credentialOptions, setCredentialOptions] = useState<
    CredentialBinding[]
  >([]);
  const [browserProfileOptions, setBrowserProfileOptions] = useState<
    BrowserProfile[]
  >([]);

  const [newCredentialAlias, setNewCredentialAlias] =
    useState("目标 Agent 测试账号");
  const [newCredentialUsername, setNewCredentialUsername] = useState("");
  const [newCredentialPassword, setNewCredentialPassword] = useState("");
  const [credentialSaving, setCredentialSaving] = useState(false);
  const [credentialMessage, setCredentialMessage] = useState("");

  const [promptInputSelector, setPromptInputSelector] = useState(
    stringValue(
      selectorsConfig.prompt_input,
      "textarea, [contenteditable='true']",
    ),
  );
  const [sendButtonSelector, setSendButtonSelector] = useState(
    stringValue(selectorsConfig.send_button, "button[type='submit']"),
  );
  const [responseSelector, setResponseSelector] = useState(
    stringValue(selectorsConfig.response_container, ""),
  );

  const [responsePath, setResponsePath] = useState(
    stringValue(config.response_path, "output"),
  );
  const [requestTemplate, setRequestTemplate] = useState(
    JSON.stringify(
      config.request_template ?? { input: "{{ input }}" },
      null,
      2,
    ),
  );

  const [timeout, setTimeoutVal] = useState(numberValue(config.timeout, 30));
  const [maxSteps, setMaxSteps] = useState(
    config.max_steps != null ? String(config.max_steps) : "20",
  );
  const [costLimit, setCostLimit] = useState(
    config.cost_limit != null ? String(config.cost_limit) : "",
  );
  const [blockedActions, setBlockedActions] = useState<string[]>(
    stringArray(safetyConfig.blocked_actions).length > 0
      ? stringArray(safetyConfig.blocked_actions)
      : [...DEFAULT_BLOCKED_ACTIONS],
  );
  const [testScope, setTestScope] = useState<TestScope>(
    safetyConfig.mode === "guided" ? "guided" : "readonly",
  );
  const [requiresConfirmation, setRequiresConfirmation] = useState(
    safetyConfig.requires_confirmation !== false,
  );

  const [model, setModel] = useState(stringValue(config.model));
  const [systemPrompt, setSystemPrompt] = useState(
    stringValue(config.system_prompt),
  );
  const [codeVersion, setCodeVersion] = useState(
    stringValue(config.code_version),
  );
  const [gitCommit, setGitCommit] = useState(stringValue(config.git_commit));
  const [modelParams, setModelParams] = useState(
    JSON.stringify(config.model_params ?? {}, null, 2),
  );
  const [tools, setTools] = useState(
    JSON.stringify(config.tools ?? [], null, 2),
  );
  const [credentialIds, setCredentialIds] = useState(
    Array.isArray(config.credential_binding_ids)
      ? config.credential_binding_ids.join(", ")
      : "",
  );
  const [systemPromptVersion, setSystemPromptVersion] = useState(
    stringValue(config.system_prompt_version),
  );
  const [knowledgeVersion, setKnowledgeVersion] = useState(
    stringValue(config.knowledge_version),
  );
  const [adapterId, setAdapterId] = useState(stringValue(config.adapter_id));
  const [adapterVersion, setAdapterVersion] = useState(
    stringValue(config.adapter_version),
  );

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    listCredentialBindings(projectId)
      .then(setCredentialOptions)
      .catch(() => setCredentialOptions([]));
    listBrowserProfiles(projectId)
      .then(setBrowserProfileOptions)
      .catch(() => setBrowserProfileOptions([]));
  }, [open, projectId]);

  async function saveInlineCredential() {
    if (
      !newCredentialAlias.trim() ||
      !newCredentialUsername.trim() ||
      !newCredentialPassword
    ) {
      setCredentialMessage("请填写凭证名称、账号和密码");
      return;
    }
    setCredentialSaving(true);
    setCredentialMessage("");
    try {
      const saved = await createCredentialBinding(projectId, {
        alias: newCredentialAlias.trim(),
        injection_location: "header",
        injection_name: "target_login",
        kind: "custom",
        value: JSON.stringify({
          password: newCredentialPassword,
          username: newCredentialUsername.trim(),
        }),
      });
      setCredentialOptions((prev) => {
        const withoutDuplicate = prev.filter((item) => item.id !== saved.id);
        return [saved, ...withoutDuplicate];
      });
      setCredentialId(saved.id);
      setLoginStrategy("credential");
      setNewCredentialUsername("");
      setNewCredentialPassword("");
      setCredentialMessage("已保存为项目凭证，版本配置只会引用凭证 ID。");
    } catch (caught) {
      setCredentialMessage(
        caught instanceof Error ? caught.message : "保存凭证失败",
      );
    } finally {
      setCredentialSaving(false);
    }
  }

  async function submit() {
    const effectiveEntryUrl = targetUrl.trim() || apiUrl.trim();
    const effectiveApiUrl = apiUrl.trim() || effectiveEntryUrl;
    if (!effectiveEntryUrl) {
      setError("请输入目标地址");
      return;
    }

    let parsedTemplate: Record<string, unknown>;
    let parsedModelParams: Record<string, string | number | boolean>;
    let parsedTools: Array<Record<string, unknown>>;
    try {
      const raw = JSON.parse(requestTemplate) as unknown;
      if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
        setError("请求模板必须是 JSON 对象");
        return;
      }
      parsedTemplate = raw as Record<string, unknown>;
      parsedModelParams = JSON.parse(modelParams) as Record<
        string,
        string | number | boolean
      >;
      parsedTools = JSON.parse(tools) as Array<Record<string, unknown>>;
      if (
        !parsedModelParams ||
        Array.isArray(parsedModelParams) ||
        !Array.isArray(parsedTools)
      )
        throw new Error();
    } catch {
      setError("请求模板、模型参数或工具清单不是合法 JSON");
      return;
    }

    if (loginStrategy === "credential" && !credentialId) {
      setError("请选择项目凭证，或先保存账号密码为项目凭证");
      setAdvancedOpen(false);
      return;
    }
    if (loginStrategy === "browser_profile" && !browserProfileId) {
      setError("请选择登录态可用的浏览器实例");
      setAdvancedOpen(false);
      return;
    }
    if (loginStrategy === "username_password") {
      setError("请先保存账号密码为项目凭证");
      return;
    }

    const metadataCredentialIds = credentialIds
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
    const effectiveCredentialIds = Array.from(
      new Set([
        ...metadataCredentialIds,
        ...(loginStrategy === "credential" && credentialId
          ? [credentialId]
          : []),
      ]),
    );
    const targetLogin =
      loginStrategy === "credential"
        ? { credential_binding_id: credentialId, strategy: "credential" }
        : loginStrategy === "browser_profile"
          ? { strategy: "browser_profile" }
          : { strategy: "none" };
    const safetyBlockedActions =
      testScope === "readonly" ? [...DEFAULT_BLOCKED_ACTIONS] : blockedActions;

    const targetConfigPayload = {
      browser_profile_id:
        loginStrategy === "browser_profile"
          ? browserProfileId || undefined
          : undefined,
      entry_url: effectiveEntryUrl,
      login: targetLogin,
      plugin_id: targetPlugin.pluginId,
      plugin_version: targetPlugin.version,
      safety_boundaries: {
        blocked_actions: safetyBlockedActions,
        mode: testScope,
        requires_confirmation: requiresConfirmation,
      },
      selectors: {
        prompt_input: promptInputSelector.trim() || undefined,
        response_container: responseSelector.trim() || undefined,
        send_button: sendButtonSelector.trim() || undefined,
      },
      target_type: targetPlugin.targetType,
    };

    setSubmitting(true);
    setError("");
    try {
      const payload: CreateAgentVersionRequest = {
        config: {
          adapter_id: adapterId.trim() || undefined,
          adapter_version: adapterVersion.trim() || undefined,
          api_url: effectiveApiUrl,
          code_version: codeVersion.trim() || undefined,
          cost_limit: costLimit ? Number(costLimit) : undefined,
          credential_binding_ids: effectiveCredentialIds,
          git_commit: gitCommit.trim() || undefined,
          knowledge_version: knowledgeVersion.trim() || undefined,
          max_steps: maxSteps ? Number(maxSteps) : undefined,
          model: model.trim() || undefined,
          model_params: parsedModelParams,
          plugin_id: targetPlugin.pluginId,
          plugin_version: targetPlugin.version,
          protocol,
          request_template: parsedTemplate,
          response_path: responsePath.trim(),
          system_prompt: systemPrompt.trim() || undefined,
          system_prompt_version: systemPromptVersion.trim() || undefined,
          target_config: targetConfigPayload,
          timeout,
          tools: parsedTools,
          web_url: effectiveEntryUrl,
        },
      };
      await onSubmit(payload);
      setOpen(false);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "保存版本失败，请检查配置后重试。",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const isEditing = version != null;

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant={version ? "secondary" : "primary"}>
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-3xl overflow-auto">
        <DialogTitle>
          {isEditing ? "编辑 Agent 版本" : "创建 Agent 版本"}
        </DialogTitle>
        <DialogDescription>
          填写目标地址和登录方式即可开始；插件、API
          和选择器参数可在高级设置中调整。
        </DialogDescription>

        <div className="mt-4 space-y-5">
          <TargetSection
            browserProfileId={browserProfileId}
            browserProfiles={browserProfileOptions}
            credentialId={credentialId}
            credentialMessage={credentialMessage}
            credentialSaving={credentialSaving}
            credentials={credentialOptions}
            loginStrategy={loginStrategy}
            newCredentialAlias={newCredentialAlias}
            newCredentialPassword={newCredentialPassword}
            newCredentialUsername={newCredentialUsername}
            onBrowserProfileIdChange={setBrowserProfileId}
            onCredentialAliasChange={setNewCredentialAlias}
            onCredentialIdChange={setCredentialId}
            onCredentialPasswordChange={setNewCredentialPassword}
            onCredentialUsernameChange={setNewCredentialUsername}
            onLoginStrategyChange={setLoginStrategy}
            onSaveCredential={saveInlineCredential}
            onTargetUrlChange={setTargetUrl}
            onTestScopeChange={setTestScope}
            targetUrl={targetUrl}
            testScope={testScope}
          />

          <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-[var(--ink)]">
                  高级设置
                </p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  插件、API、选择器、安全边界和版本元数据。
                </p>
              </div>
              <Button
                aria-expanded={advancedOpen}
                onClick={() => setAdvancedOpen((value) => !value)}
                type="button"
                variant="secondary"
              >
                {advancedOpen ? "收起高级设置" : "高级设置"}
              </Button>
            </div>

            {advancedOpen ? (
              <div className="mt-4 space-y-5 border-t border-[var(--hairline)] pt-4">
                <AdvancedConnectionSection
                  apiUrl={apiUrl}
                  onApiUrlChange={setApiUrl}
                  onTargetPluginIdChange={setTargetPluginId}
                  selectedPlugin={targetPlugin}
                  targetPluginId={targetPluginId}
                />
                <section className="space-y-4">
                  <h3 className="text-sm font-medium text-[var(--ink)]">
                    请求映射
                  </h3>
                  <MappingsSection
                    onPromptInputSelectorChange={setPromptInputSelector}
                    onRequestTemplateChange={setRequestTemplate}
                    onResponsePathChange={setResponsePath}
                    onResponseSelectorChange={setResponseSelector}
                    onSendButtonSelectorChange={setSendButtonSelector}
                    promptInputSelector={promptInputSelector}
                    requestTemplate={requestTemplate}
                    responsePath={responsePath}
                    responseSelector={responseSelector}
                    sendButtonSelector={sendButtonSelector}
                  />
                </section>
                <section className="space-y-4">
                  <h3 className="text-sm font-medium text-[var(--ink)]">
                    安全边界
                  </h3>
                  <LimitsSection
                    blockedActions={blockedActions}
                    costLimit={costLimit}
                    maxSteps={maxSteps}
                    onBlockedActionsChange={setBlockedActions}
                    onCostLimitChange={setCostLimit}
                    onMaxStepsChange={setMaxSteps}
                    onRequiresConfirmationChange={setRequiresConfirmation}
                    onTimeoutChange={setTimeoutVal}
                    requiresConfirmation={requiresConfirmation}
                    timeout={timeout}
                  />
                </section>
                <section className="space-y-4">
                  <h3 className="text-sm font-medium text-[var(--ink)]">
                    版本元数据
                  </h3>
                  <MetadataSection
                    adapterId={adapterId}
                    adapterVersion={adapterVersion}
                    codeVersion={codeVersion}
                    credentialIds={credentialIds}
                    gitCommit={gitCommit}
                    isEditing={isEditing}
                    knowledgeVersion={knowledgeVersion}
                    model={model}
                    modelParams={modelParams}
                    onAdapterIdChange={setAdapterId}
                    onAdapterVersionChange={setAdapterVersion}
                    onCodeVersionChange={setCodeVersion}
                    onCredentialIdsChange={setCredentialIds}
                    onGitCommitChange={setGitCommit}
                    onKnowledgeVersionChange={setKnowledgeVersion}
                    onModelChange={setModel}
                    onModelParamsChange={setModelParams}
                    onProtocolChange={setProtocol}
                    onSystemPromptChange={setSystemPrompt}
                    onSystemPromptVersionChange={setSystemPromptVersion}
                    onToolsChange={setTools}
                    protocol={protocol}
                    systemPrompt={systemPrompt}
                    systemPromptVersion={systemPromptVersion}
                    tools={tools}
                  />
                </section>
              </div>
            ) : null}
          </div>

          {isEditing && version.status === "draft" ? (
            <ConnectionTestPanel
              agentId={agentId}
              projectId={projectId}
              version={version}
              versionId={version.id}
            />
          ) : null}

          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}

          <div className="flex items-center justify-end border-t border-[var(--hairline)] pt-4">
            <div className="flex gap-2">
              <Button onClick={() => setOpen(false)} type="button">
                取消
              </Button>
              <Button
                disabled={submitting}
                onClick={submit}
                type="button"
                variant="primary"
              >
                {submitting ? "保存中…" : "保存并开始配置测试"}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function TargetSection({
  browserProfileId,
  browserProfiles,
  credentialId,
  credentialMessage,
  credentialSaving,
  credentials,
  loginStrategy,
  newCredentialAlias,
  newCredentialPassword,
  newCredentialUsername,
  onBrowserProfileIdChange,
  onCredentialAliasChange,
  onCredentialIdChange,
  onCredentialPasswordChange,
  onCredentialUsernameChange,
  onLoginStrategyChange,
  onSaveCredential,
  onTargetUrlChange,
  onTestScopeChange,
  targetUrl,
  testScope,
}: {
  browserProfileId: string;
  browserProfiles: BrowserProfile[];
  credentialId: string;
  credentialMessage: string;
  credentialSaving: boolean;
  credentials: CredentialBinding[];
  loginStrategy: LoginStrategy;
  newCredentialAlias: string;
  newCredentialPassword: string;
  newCredentialUsername: string;
  onBrowserProfileIdChange: (value: string) => void;
  onCredentialAliasChange: (value: string) => void;
  onCredentialIdChange: (value: string) => void;
  onCredentialPasswordChange: (value: string) => void;
  onCredentialUsernameChange: (value: string) => void;
  onLoginStrategyChange: (value: LoginStrategy) => void;
  onSaveCredential: () => Promise<void>;
  onTargetUrlChange: (value: string) => void;
  onTestScopeChange: (value: TestScope) => void;
  targetUrl: string;
  testScope: TestScope;
}) {
  return (
    <section className="space-y-4 rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--canvas-soft)] p-4">
      <div className="grid gap-3 md:grid-cols-3">
        <div>
          <label
            className="block text-sm font-medium"
            htmlFor="agent-version-target-url"
          >
            目标地址
          </label>
          <Input
            aria-label="目标地址"
            className="mt-1.5"
            id="agent-version-target-url"
            onChange={(event) => onTargetUrlChange(event.target.value)}
            placeholder="https://app.example.com/chat"
            value={targetUrl}
          />
        </div>
        <div>
          <label className="block text-sm font-medium">登录方式</label>
          <DropdownSelect
            aria-label="登录方式"
            className="mt-1.5 h-10 w-full rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
            onChange={(event) =>
              onLoginStrategyChange(event.target.value as LoginStrategy)
            }
            value={loginStrategy}
          >
            <option value="none">无需登录</option>
            <option value="browser_profile">用已登录浏览器</option>
            <option value="username_password">输入账号密码</option>
            <option value="credential">选择项目凭证</option>
          </DropdownSelect>
        </div>
        <div>
          <label className="block text-sm font-medium">测试范围</label>
          <DropdownSelect
            aria-label="测试范围"
            className="mt-1.5 h-10 w-full rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
            onChange={(event) =>
              onTestScopeChange(event.target.value as TestScope)
            }
            value={testScope}
          >
            <option value="readonly">只读安全测试</option>
            <option value="guided">人工确认交互测试</option>
          </DropdownSelect>
        </div>
      </div>
      {loginStrategy === "browser_profile" ? (
        <label className="block text-sm font-medium">
          浏览器实例
          <DropdownSelect
            aria-label="浏览器实例"
            className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
            onChange={(event) => onBrowserProfileIdChange(event.target.value)}
            value={browserProfileId}
          >
            <option value="">请选择登录态可用的浏览器实例</option>
            {browserProfiles.map((profile) => (
              <option
                disabled={profile.auth_state_status !== "ready"}
                key={profile.profile_id}
                value={profile.profile_id}
              >
                {profile.name}（
                {profile.auth_state_status === "ready"
                  ? "登录态可用"
                  : profile.auth_state_status === "expired"
                    ? "已过期"
                    : "未就绪"}
                ）
              </option>
            ))}
          </DropdownSelect>
        </label>
      ) : null}
      {loginStrategy === "credential" ? (
        <label className="block text-sm font-medium">
          项目凭证
          <DropdownSelect
            aria-label="项目凭证"
            className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
            onChange={(event) => onCredentialIdChange(event.target.value)}
            value={credentialId}
          >
            <option value="">选择已加密保存的凭证</option>
            {credentials.map((credential) => (
              <option key={credential.id} value={credential.id}>
                {credential.alias}（{credential.masked_hint}）
              </option>
            ))}
          </DropdownSelect>
        </label>
      ) : null}
      {loginStrategy === "username_password" ? (
        <div className="rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--canvas-soft)] p-4">
          <div className="grid gap-3 md:grid-cols-3">
            <label className="block text-sm font-medium">
              凭证名称
              <Input
                className="mt-1.5"
                onChange={(event) =>
                  onCredentialAliasChange(event.target.value)
                }
                value={newCredentialAlias}
              />
            </label>
            <label className="block text-sm font-medium">
              账号
              <Input
                className="mt-1.5"
                onChange={(event) =>
                  onCredentialUsernameChange(event.target.value)
                }
                value={newCredentialUsername}
              />
            </label>
            <label className="block text-sm font-medium">
              密码
              <Input
                className="mt-1.5"
                onChange={(event) =>
                  onCredentialPasswordChange(event.target.value)
                }
                type="password"
                value={newCredentialPassword}
              />
            </label>
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            <p className="text-xs text-[var(--muted)]">
              密码只发送到项目凭证接口进行加密保存，不会进入 Agent 版本配置。
            </p>
            <Button
              disabled={credentialSaving}
              onClick={() => void onSaveCredential()}
              type="button"
              variant="secondary"
            >
              {credentialSaving ? "保存中…" : "保存为项目凭证"}
            </Button>
          </div>
          {credentialMessage ? (
            <p className="mt-2 text-xs text-[var(--muted)]">
              {credentialMessage}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function AdvancedConnectionSection({
  apiUrl,
  onApiUrlChange,
  onTargetPluginIdChange,
  selectedPlugin,
  targetPluginId,
}: {
  apiUrl: string;
  onApiUrlChange: (value: string) => void;
  onTargetPluginIdChange: (value: string) => void;
  selectedPlugin: TargetPluginTemplate;
  targetPluginId: string;
}) {
  return (
    <section className="space-y-4">
      <h3 className="text-sm font-medium text-[var(--ink)]">目标连接</h3>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="block text-sm font-medium">
          目标插件
          <DropdownSelect
            aria-label="目标插件"
            className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
            onChange={(event) => onTargetPluginIdChange(event.target.value)}
            value={targetPluginId}
          >
            {TARGET_PLUGIN_TEMPLATES.map((template) => (
              <option key={template.pluginId} value={template.pluginId}>
                {template.pluginId === "tapnow-canvas-agent"
                  ? "TapNow 画布 Agent"
                  : template.pluginId === "generic-http-agent"
                    ? "通用 HTTP Agent"
                    : "通用 Web Agent"}
              </option>
            ))}
          </DropdownSelect>
          <span className="mt-1 block text-xs text-[var(--muted)]">
            {selectedPlugin.description}
          </span>
        </label>
        <label className="block text-sm font-medium">
          API 地址
          <Input
            aria-label="API 地址"
            className="mt-1.5"
            onChange={(event) => onApiUrlChange(event.target.value)}
            placeholder="留空时使用目标地址"
            value={apiUrl}
          />
        </label>
      </div>
    </section>
  );
}
function MappingsSection({
  onPromptInputSelectorChange,
  onRequestTemplateChange,
  onResponsePathChange,
  onResponseSelectorChange,
  onSendButtonSelectorChange,
  promptInputSelector,
  requestTemplate,
  responsePath,
  responseSelector,
  sendButtonSelector,
}: {
  onPromptInputSelectorChange: (value: string) => void;
  onRequestTemplateChange: (value: string) => void;
  onResponsePathChange: (value: string) => void;
  onResponseSelectorChange: (value: string) => void;
  onSendButtonSelectorChange: (value: string) => void;
  promptInputSelector: string;
  requestTemplate: string;
  responsePath: string;
  responseSelector: string;
  sendButtonSelector: string;
}) {
  return (
    <>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="block text-sm font-medium">
          输入框选择器
          <Input
            className="mt-1.5"
            onChange={(event) =>
              onPromptInputSelectorChange(event.target.value)
            }
            value={promptInputSelector}
          />
        </label>
        <label className="block text-sm font-medium">
          发送按钮选择器
          <Input
            className="mt-1.5"
            onChange={(event) => onSendButtonSelectorChange(event.target.value)}
            value={sendButtonSelector}
          />
        </label>
        <label className="block text-sm font-medium">
          回复区域选择器
          <Input
            className="mt-1.5"
            onChange={(event) => onResponseSelectorChange(event.target.value)}
            placeholder="可选"
            value={responseSelector}
          />
        </label>
      </div>
      <label className="block text-sm font-medium">
        请求模板（JSON，支持 {"{{ input }}"} 占位）
        <textarea
          className="mt-1.5 min-h-32 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] p-3 font-mono text-xs"
          onChange={(event) => onRequestTemplateChange(event.target.value)}
          value={requestTemplate}
        />
      </label>
      <label className="block text-sm font-medium">
        响应提取路径
        <Input
          className="mt-1.5"
          onChange={(event) => onResponsePathChange(event.target.value)}
          placeholder="例如 choices.0.message.content"
          value={responsePath}
        />
      </label>
    </>
  );
}

function LimitsSection({
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

function MetadataSection({
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
