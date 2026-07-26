"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

type ToastVariant = "default" | "destructive" | "success";

interface Toast {
  id: string;
  message: string;
  variant?: ToastVariant;
  duration?: number;
}

let addToastFn: ((toast: Omit<Toast, "id">) => void) | null = null;

export function toast(message: string, variant?: ToastVariant, duration?: number) {
  addToastFn?.({ message, variant, duration });
}

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    addToastFn = (t) => {
      const id = Math.random().toString(36).slice(2);
      setToasts((prev) => [...prev, { ...t, id }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== id));
      }, t.duration ?? 5000);
    };
    return () => { addToastFn = null; };
  }, []);

  const remove = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg animate-in slide-in-from-right",
            t.variant === "destructive" && "border-destructive/50 bg-destructive/10 text-destructive",
            t.variant === "success" && "border-emerald-500/50 bg-emerald-500/10 text-emerald-600",
            (!t.variant || t.variant === "default") && "border-border bg-background text-foreground"
          )}
        >
          <p className="text-sm">{t.message}</p>
          <button
            onClick={() => remove(t.id)}
            className="ml-auto shrink-0 rounded-md p-1 hover:bg-muted"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
