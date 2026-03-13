"use client";

import React, { createContext, useCallback, useContext, useState, ReactNode } from "react";
import { ToastActionElement } from "@/components/ui/toast";

type ToastVariant = "default" | "success" | "destructive";

type ToastProps = {
  id: string;
  title?: ReactNode;
  description?: ReactNode;
  action?: ToastActionElement;
  variant?: ToastVariant;
  duration?: number;
};

type ToastState = ToastProps[];

type ToastContextValue = {
  toasts: ToastState;
  toast: (props: Omit<ToastProps, "id">) => void;
  dismiss: (toastId?: string) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

let toastCount = 0;

interface ToastStateProviderProps {
  children: ReactNode;
}

export const ToastStateProvider: React.FC<ToastStateProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastState>([]);

  const dismiss = useCallback((toastId?: string) => {
    setToasts((state) =>
      toastId ? state.filter((toast) => toast.id !== toastId) : [],
    );
  }, []);

  const toast = useCallback(
    ({ duration = 4000, ...props }: Omit<ToastProps, "id">) => {
      const id = `toast-${toastCount++}`;
      setToasts((state) => [{ id, ...props }, ...state].slice(0, 4));

      if (duration > 0) {
        window.setTimeout(() => {
          dismiss(id);
        }, duration);
      }
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
    </ToastContext.Provider>
  );
};

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastStateProvider");
  }
  return context;
}
