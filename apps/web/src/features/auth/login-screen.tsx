"use client";

import { useRouter } from "next/navigation";

import { LoginForm } from "./login-form";

export function LoginScreen({ returnTo }: { returnTo?: string }) {
  const router = useRouter();
  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      {/* 左侧品牌区域 */}
      <aside
        className="relative hidden overflow-hidden lg:flex lg:flex-col lg:justify-between lg:p-14"
        style={{
          background:
            "linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 70%, #1a1a2e) 100%)",
        }}
      >
        {/* 装饰性背景图案 */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 20%, white 1px, transparent 1px)",
            backgroundSize: "60px 60px, 100px 100px",
          }}
        />
        <div className="relative">
          <p className="text-sm font-semibold tracking-wide text-white/70">
            Warmy Agent Test
          </p>
        </div>
        <div className="relative max-w-md">
          <blockquote className="text-3xl font-semibold leading-snug tracking-tight text-white">
            “统一测试、
            <br />
            安全评估、
            <br />
            持续交付。”
          </blockquote>
          <p className="mt-6 text-base leading-relaxed text-white/65">
            面向 AI Agent 的自动化测试平台。首批支持画布 Agent，
            后续通过插件扩展客服、浏览器、工作流等场景。
          </p>
        </div>
        <p className="relative text-xs text-white/40">
          {"©"} {new Date().getFullYear()} Warmy. 仅供内部使用。
        </p>
      </aside>

      {/* 右侧登录表单 */}
      <section className="flex items-center justify-center px-6 py-14 lg:px-16">
        <div className="w-full max-w-[400px] opacity-100 transition-all duration-700">
          {/* 移动端品牌标识 */}
          <div className="mb-10 lg:hidden">
            <p className="text-sm font-semibold tracking-wide text-[var(--accent)]">
              Warmy Agent Test
            </p>
          </div>

          <h1 className="text-[1.75rem] font-semibold tracking-tight leading-tight">
            登录到测试工作台
          </h1>
          <p className="mt-2.5 text-sm leading-relaxed text-[var(--text-muted)]">
            使用内部账号继续。平台暂不开放自主注册。
          </p>

          <div className="mt-8">
            <LoginForm
              onSuccess={(path) => router.replace(path)}
              returnTo={returnTo}
            />
          </div>

          <p className="mt-8 text-center text-xs text-[var(--text-subtle)]">
            安全连接 · 数据加密传输
          </p>
        </div>
      </section>
    </main>
  );
}
