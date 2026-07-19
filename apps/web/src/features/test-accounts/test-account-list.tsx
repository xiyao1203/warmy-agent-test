"use client";

import { Eye, EyeOff, Plus, Trash2, User } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownSelect } from "@/components/ui/dropdown-select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/uiverse";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  TableActionButton,
  TableActions,
  tableActionHeadClass,
} from "@/components/ui/table-actions";
import { TruncatedText } from "@/components/ui/truncated-text";

type TestAccount = {
  id: string;
  name: string;
  username: string;
  credential_masked: string;
  account_type: string;
  enabled: boolean;
  description?: string | null;
  created_at: string;
};

type TestAccountListProps = {
  accounts?: TestAccount[];
  loading?: boolean;
  onCreate?: (payload: {
    name: string;
    username: string;
    credential_encrypted: string;
    account_type: string;
    description?: string;
  }) => Promise<unknown>;
  onDelete?: (accountId: string) => Promise<unknown>;
  onToggleEnabled?: (accountId: string, enabled: boolean) => Promise<unknown>;
  projectId: string;
};

const typeLabels: Record<string, string> = {
  user: "普通用户",
  admin: "管理员",
  service: "服务账号",
  api: "API 账号",
};

export function TestAccountList({
  accounts = [],
  loading = false,
  onCreate,
  onDelete,
  onToggleEnabled,
}: TestAccountListProps) {
  if (loading) {
    return (
      <div className="mt-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-6 w-28" />
            <Skeleton className="mt-1.5 h-4 w-56" />
          </div>
        </div>
        <section className="mt-4 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton
              className="h-11 w-full border-b border-[var(--hairline)] last:border-b-0"
              key={i}
            />
          ))}
        </section>
      </div>
    );
  }

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">测试账号</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            管理用于测试的账号凭证，凭证已加密存储。
          </p>
        </div>
        {onCreate && <CreateAccountDialog onCreate={onCreate} />}
      </div>

      <section className="mt-4 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--hairline)] bg-[var(--surface)]">
        {!accounts.length ? (
          <EmptyState
            description="创建测试账号后，可在测试计划中引用。"
            title="暂无测试账号"
          />
        ) : (
          <Table>
            <TableHeader className="bg-[var(--canvas-soft)]">
              <TableRow>
                <TableHead className="min-w-52">账号信息</TableHead>
                <TableHead className="whitespace-nowrap">类型</TableHead>
                <TableHead className="min-w-40 whitespace-nowrap">
                  凭证（掩码）
                </TableHead>
                <TableHead className="whitespace-nowrap">状态</TableHead>
                <TableHead className={tableActionHeadClass}>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {accounts.map((account) => (
                <TableRow
                  className="transition-colors hover:bg-[var(--canvas-soft)]"
                  key={account.id}
                >
                  <TableCell>
                    <div className="mx-auto flex w-fit items-center gap-3 text-left">
                      <span className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--canvas-soft)]">
                        <User aria-hidden="true" className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <TruncatedText className="font-medium">
                          {account.name}
                        </TruncatedText>
                        <TruncatedText className="mt-0.5 text-xs text-[var(--muted)]">
                          {account.username}
                        </TruncatedText>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge>
                      {typeLabels[account.account_type] ?? account.account_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    <code className="rounded bg-[var(--canvas-soft)] px-2 py-1 text-xs">
                      {account.credential_masked}
                    </code>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge tone={account.enabled ? "success" : "neutral"}>
                      {account.enabled ? "启用" : "禁用"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    <TableActions label={account.name}>
                      {onToggleEnabled && (
                        <TableActionButton
                          accessibleLabel={`${account.enabled ? "禁用" : "启用"}测试账号 ${account.name}`}
                          label={account.enabled ? "禁用" : "启用"}
                          onClick={() =>
                            onToggleEnabled(account.id, !account.enabled)
                          }
                        >
                          {account.enabled ? (
                            <EyeOff aria-hidden="true" className="size-4" />
                          ) : (
                            <Eye aria-hidden="true" className="size-4" />
                          )}
                        </TableActionButton>
                      )}
                      {onDelete && (
                        <TableActionButton
                          accessibleLabel={`删除测试账号 ${account.name}`}
                          label="删除"
                          onClick={() => onDelete(account.id)}
                          tone="danger"
                        >
                          <Trash2
                            aria-hidden="true"
                            className="size-4 text-[var(--danger)]"
                          />
                        </TableActionButton>
                      )}
                    </TableActions>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>
    </div>
  );
}

/* ── 创建账号对话框 ────────────────────────────────────────────────── */

function CreateAccountDialog({
  onCreate,
}: {
  onCreate: (payload: {
    name: string;
    username: string;
    credential_encrypted: string;
    account_type: string;
    description?: string;
  }) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [credential, setCredential] = useState("");
  const [accountType, setAccountType] = useState("user");
  const [description, setDescription] = useState("");
  const [showCredential, setShowCredential] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim() || !username.trim() || !credential.trim()) {
      setError("请填写必填字段");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({
        name: name.trim(),
        username: username.trim(),
        credential_encrypted: credential.trim(),
        account_type: accountType,
        description: description.trim() || undefined,
      });
      setOpen(false);
      resetForm();
    } catch {
      setError("创建失败，请检查输入后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  function resetForm() {
    setName("");
    setUsername("");
    setCredential("");
    setAccountType("user");
    setDescription("");
    setError("");
    setShowCredential(false);
  }

  return (
    <Dialog
      onOpenChange={(open) => {
        setOpen(open);
        if (!open) resetForm();
      }}
      open={open}
    >
      <DialogTrigger asChild>
        <Button variant="primary">
          <Plus aria-hidden="true" className="mr-1.5 size-4" />
          创建测试账号
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>创建测试账号</DialogTitle>
        <DialogDescription>
          凭证将加密存储，API 响应中仅显示掩码。
        </DialogDescription>
        <div className="mt-5 space-y-4">
          <label className="block text-sm font-medium">
            账号名称 <span className="text-[var(--danger)]">*</span>
            <Input
              className="mt-1.5"
              onChange={(e) => setName(e.target.value)}
              placeholder="如：测试管理员"
              value={name}
            />
          </label>
          <label className="block text-sm font-medium">
            用户名 <span className="text-[var(--danger)]">*</span>
            <Input
              className="mt-1.5"
              onChange={(e) => setUsername(e.target.value)}
              placeholder="如：test_admin"
              value={username}
            />
          </label>
          <label className="block text-sm font-medium">
            凭证（密码/Token） <span className="text-[var(--danger)]">*</span>
            <div className="relative mt-1.5">
              <Input
                onChange={(e) => setCredential(e.target.value)}
                placeholder="输入凭证"
                type={showCredential ? "text" : "password"}
                value={credential}
              />
              <button
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
                onClick={() => setShowCredential(!showCredential)}
                type="button"
              >
                {showCredential ? (
                  <EyeOff className="size-4" />
                ) : (
                  <Eye className="size-4" />
                )}
              </button>
            </div>
          </label>
          <label className="block text-sm font-medium">
            账号类型
            <DropdownSelect
              className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--hairline)] bg-[var(--surface)] px-3"
              onChange={(e) => setAccountType(e.target.value)}
              value={accountType}
            >
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
              <option value="service">服务账号</option>
              <option value="api">API 账号</option>
            </DropdownSelect>
          </label>
          <label className="block text-sm font-medium">
            描述
            <Input
              className="mt-1.5"
              onChange={(e) => setDescription(e.target.value)}
              placeholder="可选描述"
              value={description}
            />
          </label>
          {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
          <div className="flex justify-end gap-2 border-t border-[var(--hairline)] pt-4">
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button
              disabled={submitting}
              loading={submitting}
              onClick={submit}
              variant="primary"
            >
              创建账号
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
