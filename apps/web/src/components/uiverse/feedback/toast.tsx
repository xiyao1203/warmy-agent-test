"use client";

import { AlertCircle, CheckCircle, Info, X, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

type ToastType = "error" | "info" | "success" | "warning";

type ToastProps = {
  message: string;
  onClose: () => void;
  type?: ToastType;
  duration?: number;
};

const typeConfig = {
  error: {
    border: "border-[var(--danger)]",
    icon: XCircle,
    iconColor: "text-[var(--danger)]",
    textColor: "text-[var(--danger)]",
  },
  info: {
    border: "border-[var(--info)]",
    icon: Info,
    iconColor: "text-[var(--info)]",
    textColor: "text-[var(--info)]",
  },
  success: {
    border: "border-[var(--success)]",
    icon: CheckCircle,
    iconColor: "text-[var(--success)]",
    textColor: "text-[var(--success)]",
  },
  warning: {
    border: "border-[var(--warning)]",
    icon: AlertCircle,
    iconColor: "text-[var(--warning)]",
    textColor: "text-[var(--warning)]",
  },
};

export function Toast({
  duration = 5000,
  message,
  onClose,
  type = "info",
}: ToastProps) {
  const config = typeConfig[type];
  const Icon = config.icon;

  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div
      className={`flex items-center gap-3 rounded-[var(--radius-md)] border border-l-2 bg-[var(--surface-raised)] p-4 shadow-[var(--shadow-overlay)] ${config.border}`}
    >
      <Icon className={`size-5 shrink-0 ${config.iconColor}`} />
      <p className={`text-sm font-medium ${config.textColor}`}>{message}</p>
      <button
        aria-label="关闭通知"
        className={`ml-auto shrink-0 rounded-[var(--radius-sm)] p-1 hover:bg-[var(--canvas-soft)] ${config.textColor}`}
        onClick={onClose}
      >
        <X className="size-4" />
      </button>
    </div>
  );
}

export function useToast() {
  const [toasts, setToasts] = useState<
    Array<{ id: number; message: string; type: ToastType }>
  >([]);

  const addToast = useCallback((message: string, type: ToastType = "info") => {
    setToasts((prev) => [...prev, { id: Date.now(), message, type }]);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return { addToast, removeToast, toasts };
}
