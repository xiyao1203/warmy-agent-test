import type {
  CreateAgentVersionRequest,
  InvocationProtocol,
} from "@warmy/generated-api-client";

export type LoginStrategy =
  | "browser_profile"
  | "credential"
  | "none"
  | "username_password";
export type TestScope = "guided" | "readonly";

export type TargetPluginTemplate = {
  description: string;
  pluginId: string;
  targetType: "web_agent" | "api_agent";
  version: string;
};

export const TARGET_PLUGIN_TEMPLATES: TargetPluginTemplate[] = [
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

export const PROTOCOL_LABELS: Record<InvocationProtocol, string> = {
  async_poll: "异步轮询",
  openai_chat: "OpenAI Chat Compatible",
  sse: "SSE 流式",
  sync_json: "同步 JSON",
};

export const DEFAULT_BLOCKED_ACTIONS = [
  "delete",
  "payment",
  "publish",
  "permission_change",
] as const;

export function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export function stringValue(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

export function stringArray(value: unknown) {
  return Array.isArray(value) ? value.map(String) : [];
}

export function numberValue(value: unknown, fallback: number) {
  return typeof value === "number" ? value : fallback;
}

export function selectedTemplate(pluginId: string) {
  return (
    TARGET_PLUGIN_TEMPLATES.find(
      (template) => template.pluginId === pluginId,
    ) ?? TARGET_PLUGIN_TEMPLATES[0]
  );
}

type BuildAgentVersionPayloadInput = {
  adapterId: string;
  adapterVersion: string;
  apiUrl: string;
  blockedActions: string[];
  browserProfileId: string;
  codeVersion: string;
  costLimit: string;
  credential: {
    bindingId?: string;
    password?: string;
    username?: string;
  };
  credentialBindingIds: string[];
  entryUrl: string;
  gitCommit: string;
  knowledgeVersion: string;
  loginStrategy: LoginStrategy;
  maxSteps: string;
  model: string;
  modelParams: Record<string, string | number | boolean>;
  plugin: TargetPluginTemplate;
  promptInputSelector: string;
  protocol: InvocationProtocol;
  requestTemplate: Record<string, unknown>;
  requiresConfirmation: boolean;
  responsePath: string;
  responseSelector: string;
  sendButtonSelector: string;
  systemPrompt: string;
  systemPromptVersion: string;
  testScope: TestScope;
  timeout: number;
  tools: Array<Record<string, unknown>>;
};

export function buildAgentVersionPayload({
  adapterId,
  adapterVersion,
  apiUrl,
  blockedActions,
  browserProfileId,
  codeVersion,
  costLimit,
  credential,
  credentialBindingIds,
  entryUrl,
  gitCommit,
  knowledgeVersion,
  loginStrategy,
  maxSteps,
  model,
  modelParams,
  plugin,
  promptInputSelector,
  protocol,
  requestTemplate,
  requiresConfirmation,
  responsePath,
  responseSelector,
  sendButtonSelector,
  systemPrompt,
  systemPromptVersion,
  testScope,
  timeout,
  tools,
}: BuildAgentVersionPayloadInput): CreateAgentVersionRequest {
  const effectiveCredentialIds = Array.from(
    new Set([
      ...credentialBindingIds,
      ...(loginStrategy === "credential" && credential.bindingId
        ? [credential.bindingId]
        : []),
    ]),
  );
  const targetLogin =
    loginStrategy === "credential"
      ? {
          credential_binding_id: credential.bindingId,
          strategy: "credential" as const,
        }
      : loginStrategy === "browser_profile"
        ? { strategy: "browser_profile" as const }
        : { strategy: "none" as const };
  const safetyBlockedActions =
    testScope === "readonly" ? [...DEFAULT_BLOCKED_ACTIONS] : blockedActions;

  return {
    config: {
      adapter_id: adapterId.trim() || undefined,
      adapter_version: adapterVersion.trim() || undefined,
      api_url: apiUrl,
      code_version: codeVersion.trim() || undefined,
      cost_limit: costLimit ? Number(costLimit) : undefined,
      credential_binding_ids: effectiveCredentialIds,
      git_commit: gitCommit.trim() || undefined,
      knowledge_version: knowledgeVersion.trim() || undefined,
      max_steps: maxSteps ? Number(maxSteps) : undefined,
      model: model.trim() || undefined,
      model_params: modelParams,
      plugin_id: plugin.pluginId,
      plugin_version: plugin.version,
      protocol,
      request_template: requestTemplate,
      response_path: responsePath.trim(),
      system_prompt: systemPrompt.trim() || undefined,
      system_prompt_version: systemPromptVersion.trim() || undefined,
      target_config: {
        browser_profile_id:
          loginStrategy === "browser_profile"
            ? browserProfileId || undefined
            : undefined,
        entry_url: entryUrl,
        login: targetLogin,
        plugin_id: plugin.pluginId,
        plugin_version: plugin.version,
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
        target_type: plugin.targetType,
      },
      timeout,
      tools,
      web_url: entryUrl,
    },
  };
}
