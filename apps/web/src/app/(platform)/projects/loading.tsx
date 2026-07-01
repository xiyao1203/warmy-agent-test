import { SkeletonCard } from "@/components/uiverse";

export default function PlatformLoading() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="w-full max-w-6xl space-y-6 p-8">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 animate-pulse rounded-[var(--radius-md)] bg-[var(--canvas-soft)]" />
          <div className="h-9 w-24 animate-pulse rounded-[var(--radius)] bg-[var(--canvas-soft)]" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
