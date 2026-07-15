import type {
  CreateEnvironmentVersionRequest,
  EnvironmentTemplateResponse,
  EnvironmentVersionResponse,
  UpdateEnvironmentVersionRequest,
} from "@warmy/generated-api-client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CredentialBinding } from "./api";
import type { EnvironmentListProps } from "./environment-list";
import { EnvironmentVersionDialog } from "./environment-version-dialog";

export function EnvironmentVersionPanel({
  credentials,
  draftVersion,
  onCreateVersion,
  onPublishVersion,
  onUpdateVersion,
  publishedCount,
  template,
  versions,
}: {
  credentials: CredentialBinding[];
  draftVersion?: EnvironmentVersionResponse;
  onCreateVersion?: EnvironmentListProps["onCreateVersion"];
  onPublishVersion?: EnvironmentListProps["onPublishVersion"];
  onUpdateVersion?: EnvironmentListProps["onUpdateVersion"];
  publishedCount: number;
  template: EnvironmentTemplateResponse;
  versions: EnvironmentVersionResponse[];
}) {
  return (
    <div className="rounded border border-[var(--hairline)] bg-[var(--canvas-soft)] p-4 text-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">
          版本历史 · {publishedCount} 个已发布
          {draftVersion ? " · 1 个草稿" : ""}
        </h3>
        {onCreateVersion ? (
          <EnvironmentVersionDialog
            credentials={credentials}
            key={draftVersion?.id ?? "new"}
            triggerLabel={draftVersion ? "编辑草稿" : "创建版本"}
            version={draftVersion}
            onSubmit={
              draftVersion
                ? async (payload: UpdateEnvironmentVersionRequest) => {
                    if (onUpdateVersion) {
                      await onUpdateVersion(
                        template.id,
                        draftVersion.id,
                        payload,
                      );
                    }
                  }
                : async (payload: CreateEnvironmentVersionRequest) => {
                    await onCreateVersion(template.id, payload);
                  }
            }
          />
        ) : null}
      </div>

      {versions.length === 0 ? (
        <p className="text-[var(--muted)]">
          尚无版本。点击上方按钮创建第一个版本。
        </p>
      ) : (
        <div className="space-y-2">
          {versions.map((version) => (
            <div
              className="flex items-center justify-between rounded border border-[var(--hairline)] bg-[var(--surface)] p-3"
              key={version.id}
            >
              <div className="flex items-center gap-3">
                <Badge
                  tone={version.status === "published" ? "accent" : "neutral"}
                >
                  v{version.version_number}
                </Badge>
                <Badge
                  tone={version.status === "published" ? "accent" : "neutral"}
                >
                  {version.status === "published" ? "已发布" : "草稿"}
                </Badge>
                <span className="text-xs text-[var(--muted)]">
                  {new Date(version.updated_at).toLocaleDateString("zh-CN")}
                </span>
              </div>
              <div className="flex gap-1">
                {version.status === "draft" && onUpdateVersion ? (
                  <EnvironmentVersionDialog
                    credentials={credentials}
                    triggerLabel="编辑"
                    version={version}
                    onSubmit={async (
                      payload: UpdateEnvironmentVersionRequest,
                    ) => {
                      await onUpdateVersion(template.id, version.id, payload);
                    }}
                  />
                ) : null}
                {version.status === "draft" && onPublishVersion ? (
                  <Button
                    onClick={() => onPublishVersion(template.id, version.id)}
                    variant="primary"
                  >
                    发布
                  </Button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
