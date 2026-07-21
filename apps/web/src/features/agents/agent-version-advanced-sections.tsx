import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";
import {
  TARGET_PLUGIN_TEMPLATES,
  type TargetPluginTemplate,
} from "./agent-version-form";

export function AdvancedConnectionSection({
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

export function MappingsSection({
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
          className="text-code mt-1.5 min-h-32 w-full rounded border border-[var(--hairline)] bg-[var(--surface)] p-3"
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
