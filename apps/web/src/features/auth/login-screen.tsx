"use client";

import { useRouter } from "next/navigation";

import { LoginForm } from "./login-form";

export function LoginScreen({ returnTo }: { returnTo?: string }) {
  const router = useRouter();

  return (
    <main className="grid min-h-screen place-items-center bg-[var(--background)] px-4 py-10">
      <section className="w-full max-w-sm">
        <div className="mb-8">
          <p className="text-sm font-semibold">Warmy Agent Test</p>
          <h1 className="mt-6 text-2xl font-semibold tracking-tight">
            登录到测试工作台
          </h1>
          <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
            使用内部账号继续。平台暂不开放自主注册。
          </p>
        </div>
        <div className="border-t border-[var(--border)] pt-6">
          <LoginForm
            onSuccess={(path) => router.replace(path)}
            returnTo={returnTo}
          />
        </div>
      </section>
    </main>
  );
}
