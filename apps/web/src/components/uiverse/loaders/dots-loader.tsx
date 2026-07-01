import type { HTMLAttributes } from "react";

type DotsLoaderProps = HTMLAttributes<HTMLDivElement> & {
  size?: "lg" | "md" | "sm";
};

const sizeClasses = {
  lg: "gap-2",
  md: "gap-1.5",
  sm: "gap-1",
};

const dotSizeClasses = {
  lg: "size-3",
  md: "size-2",
  sm: "size-1.5",
};

export function DotsLoader({
  className = "",
  size = "md",
  ...props
}: DotsLoaderProps) {
  return (
    <div
      className={`flex items-center ${sizeClasses[size]} ${className}`}
      role="status"
      {...props}
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`animate-bounce rounded-full bg-[var(--primary)] ${dotSizeClasses[size]}`}
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
      <span className="sr-only">加载中...</span>
    </div>
  );
}
