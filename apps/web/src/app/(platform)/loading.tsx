import { Spinner } from "@/components/uiverse";

export default function PlatformLoading() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="lg" />
        <p className="text-sm text-[var(--muted)]">加载中...</p>
      </div>
    </div>
  );
}
