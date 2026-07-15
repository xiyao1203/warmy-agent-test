import type { CreateEnvironmentTemplateRequest } from "@warmy/generated-api-client";
import { Plus, Trash2 } from "lucide-react";
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
import { TableActionButton } from "@/components/ui/table-actions";
import type { CredentialBinding } from "./api";

type KeyValueRow = { id: string; key: string; value: string };

function newId() {
  return Math.random().toString(36).slice(2, 10);
}

function rowsToRecord(rows: KeyValueRow[]) {
  return rows.reduce<Record<string, string>>((result, row) => {
    const key = row.key.trim();
    if (key) result[key] = row.value.trim();
    return result;
  }, {});
}

export function CreateEnvironmentDialog({
  credentials,
  onCreate,
}: {
  credentials: CredentialBinding[];
  onCreate: (payload: CreateEnvironmentTemplateRequest) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [variableRows, setVariableRows] = useState<KeyValueRow[]>([]);
  const [headerRows, setHeaderRows] = useState<KeyValueRow[]>([]);
  const [initialStateRows, setInitialStateRows] = useState<KeyValueRow[]>([]);
  const [credentialIds, setCredentialIds] = useState<string[]>([]);

  async function submit() {
    if (!name.trim()) {
      setError("请输入模板名称");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({
        config: {
          variables: rowsToRecord(variableRows),
          headers: rowsToRecord(headerRows),
          initial_state: rowsToRecord(initialStateRows),
          credential_binding_ids: credentialIds,
          sandbox: {},
        },
        description: description.trim() || null,
        name: name.trim(),
        template_type: "blank",
      });
      setOpen(false);
      setName("");
      setDescription("");
      setVariableRows([]);
      setHeaderRows([]);
      setInitialStateRows([]);
      setCredentialIds([]);
      setError("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "创建失败，请检查输入后重试。",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog onOpenChange={setOpen} open={open}>
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          新建环境
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>新建环境</DialogTitle>
        <DialogDescription>
          新建后可绑定凭证并发布版本，测试计划会选择已发布环境执行。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            模板名称
            <Input
              className="mt-1.5"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="block text-sm font-medium">
            描述
            <Input
              className="mt-1.5"
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </label>
          <KeyValueEditor
            addLabel="添加变量"
            emptyText="没有环境变量时可以留空。"
            keyPlaceholder="变量名，例如 BASE_URL"
            label="环境变量"
            onChange={setVariableRows}
            rows={variableRows}
            valuePlaceholder="变量值，例如 https://staging.example.com"
          />
          <div>
            <p className="text-sm font-medium">凭证绑定</p>
            <div className="mt-2 space-y-2">
              {credentials.map((credential) => (
                <label
                  className="flex items-center gap-2 text-sm"
                  key={credential.id}
                >
                  <input
                    checked={credentialIds.includes(credential.id)}
                    onChange={(event) =>
                      setCredentialIds((current) =>
                        event.target.checked
                          ? [...current, credential.id]
                          : current.filter((id) => id !== credential.id),
                      )
                    }
                    type="checkbox"
                  />
                  {credential.alias} · {credential.masked_hint}
                </label>
              ))}
              {!credentials.length ? (
                <p className="text-sm text-[var(--muted)]">
                  还没有凭证。可以先创建环境，稍后再配置环境时绑定凭证。
                </p>
              ) : null}
            </div>
          </div>
          <KeyValueEditor
            addLabel="添加 Header"
            emptyText="公开 Header 不包含密钥；密钥请使用上方凭证绑定。"
            keyPlaceholder="Header 名称，例如 X-Env"
            label="公开请求头"
            onChange={setHeaderRows}
            rows={headerRows}
            valuePlaceholder="Header 值"
          />
          <KeyValueEditor
            addLabel="添加状态"
            emptyText="没有初始业务状态时可以留空。"
            keyPlaceholder="状态名，例如 workspace_id"
            label="初始业务状态"
            onChange={setInitialStateRows}
            rows={initialStateRows}
            valuePlaceholder="状态值"
          />
          {error ? (
            <p className="text-sm text-[var(--danger)]">{error}</p>
          ) : null}
          <div className="flex justify-end gap-2">
            <Button
              disabled={submitting}
              onClick={() => setOpen(false)}
              type="button"
            >
              取消
            </Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              type="button"
              variant="primary"
            >
              新建环境
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function KeyValueEditor({
  addLabel,
  emptyText,
  keyPlaceholder,
  label,
  onChange,
  rows,
  valuePlaceholder,
}: {
  addLabel: string;
  emptyText: string;
  keyPlaceholder: string;
  label: string;
  onChange: (rows: KeyValueRow[]) => void;
  rows: KeyValueRow[];
  valuePlaceholder: string;
}) {
  function updateRow(id: string, patch: Partial<KeyValueRow>) {
    onChange(rows.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-sm font-medium">{label}</p>
        <Button
          className="h-8 px-2 text-xs"
          onClick={() =>
            onChange([...rows, { id: newId(), key: "", value: "" }])
          }
          type="button"
          variant="secondary"
        >
          <Plus aria-hidden="true" className="mr-1 size-3.5" />
          {addLabel}
        </Button>
      </div>
      {rows.length ? (
        <div className="space-y-2">
          {rows.map((row) => (
            <div className="grid grid-cols-[1fr_1fr_auto] gap-2" key={row.id}>
              <Input
                aria-label={`${label}名称`}
                onChange={(event) =>
                  updateRow(row.id, { key: event.target.value })
                }
                placeholder={keyPlaceholder}
                value={row.key}
              />
              <Input
                aria-label={`${label}值`}
                onChange={(event) =>
                  updateRow(row.id, { value: event.target.value })
                }
                placeholder={valuePlaceholder}
                value={row.value}
              />
              <TableActionButton
                label={`删除${label}`}
                onClick={() =>
                  onChange(rows.filter((item) => item.id !== row.id))
                }
                tone="danger"
              >
                <Trash2 aria-hidden="true" />
              </TableActionButton>
            </div>
          ))}
        </div>
      ) : (
        <p className="rounded border border-dashed border-[var(--hairline)] p-3 text-sm text-[var(--muted)]">
          {emptyText}
        </p>
      )}
    </div>
  );
}
