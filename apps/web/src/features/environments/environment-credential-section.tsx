import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { CredentialBinding } from "./api";

type CreateCredentialPayload = {
  alias: string;
  kind: string;
  injection_location: string;
  injection_name: string;
  value: string;
};

export function EnvironmentCredentialSection({
  credentials,
  onCreate,
}: {
  credentials: CredentialBinding[];
  onCreate: (payload: CreateCredentialPayload) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [alias, setAlias] = useState("");
  const [name, setName] = useState("Authorization");
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  return (
    <section className="mt-6 rounded border border-[var(--hairline)] bg-[var(--surface)] p-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold">凭证库</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">
            添加后可绑定到环境，测试执行时按 Header 自动注入；列表和 API
            永不返回明文。
          </p>
        </div>
        <Button onClick={() => setOpen(true)} variant="secondary">
          添加凭证
        </Button>
      </div>
      {credentials.length ? (
        <ul className="mt-4 space-y-2 text-sm">
          {credentials.map((item) => (
            <li
              className="flex justify-between rounded border border-[var(--hairline)] p-3"
              key={item.id}
            >
              <span>
                {item.alias} · {item.injection_location}:{item.injection_name}
              </span>
              <code>{item.masked_hint}</code>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 rounded border border-dashed border-[var(--hairline)] p-4 text-sm text-[var(--muted)]">
          暂无凭证。添加一次后，在新建环境或配置环境时勾选即可。
        </p>
      )}
      <Dialog onOpenChange={setOpen} open={open}>
        <DialogContent>
          <DialogTitle>添加凭证</DialogTitle>
          <DialogDescription>
            凭证值保存后不可读取，只会在测试执行时注入。
          </DialogDescription>
          <div className="mt-4 space-y-3">
            <label className="block text-sm font-medium">
              凭证名称
              <Input
                className="mt-1.5"
                onChange={(event) => setAlias(event.target.value)}
                placeholder="例如 Staging API Token"
                value={alias}
              />
            </label>
            <label className="block text-sm font-medium">
              注入到哪个 Header
              <Input
                className="mt-1.5"
                onChange={(event) => setName(event.target.value)}
                placeholder="例如 Authorization"
                value={name}
              />
            </label>
            <label className="block text-sm font-medium">
              凭证值
              <Input
                className="mt-1.5"
                onChange={(event) => setValue(event.target.value)}
                placeholder="只保存一次，之后不可查看明文"
                type="password"
                value={value}
              />
            </label>
            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
            <div className="flex justify-end gap-2">
              <Button onClick={() => setOpen(false)}>取消</Button>
              <Button
                onClick={async () => {
                  try {
                    await onCreate({
                      alias,
                      kind: "bearer",
                      injection_location: "header",
                      injection_name: name,
                      value,
                    });
                    setOpen(false);
                    setAlias("");
                    setValue("");
                  } catch (caught) {
                    setError(
                      caught instanceof Error ? caught.message : "保存失败",
                    );
                  }
                }}
                variant="primary"
              >
                保存
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}
