import type { BrowserProfile } from "@/features/browser-profiles";
import type { CredentialBinding } from "@/features/environments";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import { Input } from "@/components/ui/input";
import type { LoginStrategy, TestScope } from "./agent-version-form";

type TargetSectionProps = {
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
};

export function TargetSection({
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
}: TargetSectionProps) {
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
