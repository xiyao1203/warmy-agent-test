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
    bg: "bg-red-50 dark:bg-red-950/50",
    border: "border-red-200 dark:border-red-800",
    icon: XCircle,
    iconColor: "text-red-500",
    textColor: "text-red-800 dark:text-red-200",
  },
  info: {
    bg: "bg-blue-50 dark:bg-blue-950/50",
    border: "border-blue-200 dark:border-blue-800",
    icon: Info,
    iconColor: "text-blue-500",
    textColor: "text-blue-800 dark:text-blue-200",
  },
  success: {
    bg: "bg-emerald-50 dark:bg-emerald-950/50",
    border: "border-emerald-200 dark:border-emerald-800",
    icon: CheckCircle,
    iconColor: "text-emerald-500",
    textColor: "text-emerald-800 dark:text-emerald-200",
  },
  warning: {
    bg: "bg-amber-50 dark:bg-amber-950/50",
    border: "border-amber-200 dark:border-amber-800",
    icon: AlertCircle,
    iconColor: "text-amber-500",
    textColor: "text-amber-800 dark:text-amber-200",
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
      className={`flex items-center gap-3 rounded-[var(--radius)] border p-4 shadow-lg ${config.bg} ${config.border}`}
    >
      <Icon className={`size-5 shrink-0 ${config.iconColor}`} />
      <p className={`text-sm font-medium ${config.textColor}`}>{message}</p>
      <button
        className={`ml-auto shrink-0 rounded-full p-1 hover:bg-black/5 dark:hover:bg-white/5 ${config.textColor}`}
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
