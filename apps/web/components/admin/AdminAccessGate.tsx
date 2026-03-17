"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { isAxiosError } from "axios";
import { AlertTriangle, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";

type AuthStatusResponse = {
  authenticated: boolean;
  user?: {
    id: string;
    email: string;
    name?: string | null;
    role: string;
  } | null;
};

type GateState =
  | { status: "loading" }
  | { status: "denied"; message: string; role?: string | null }
  | { status: "allowed"; role?: string | null };

export default function AdminAccessGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const [state, setState] = useState<GateState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    const checkAccess = async () => {
      try {
        const response =
          await apiClient.get<AuthStatusResponse>("/auth/status");
        if (!active) return;

        const role = response.data.user?.role ?? null;
        if (response.data.authenticated && role === "ADMIN") {
          setState({ status: "allowed", role });
          return;
        }

        setState({
          status: "denied",
          role,
          message:
            "Admin access is required for this section. Please sign in with an admin account.",
        });
      } catch (err: unknown) {
        if (!active) return;
        const message = isAxiosError(err)
          ? ((err.response?.data as { detail?: string } | undefined)?.detail ??
            "Please sign in with an admin account.")
          : "Please sign in with an admin account.";
        setState({ status: "denied", message });
      }
    };

    void checkAccess();
    return () => {
      active = false;
    };
  }, []);

  if (state.status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050505] text-white">
        <div className="text-center">
          <div className="mb-3 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
          </div>
          <p className="text-sm text-gray-400">Checking admin access...</p>
        </div>
      </div>
    );
  }

  if (state.status === "denied") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-white/5 p-8 text-center shadow-2xl shadow-black/40">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/20">
            <AlertTriangle className="h-7 w-7 text-red-300" />
          </div>
          <h1 className="text-xl font-semibold">Access denied</h1>
          <p className="mt-2 text-sm text-gray-400">{state.message}</p>
          {state.role && (
            <p className="mt-3 text-xs text-gray-500">
              Current role: <span className="text-gray-300">{state.role}</span>
            </p>
          )}
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/login"
              className="rounded-xl bg-orange-500 px-4 py-2 text-sm font-semibold text-black transition hover:bg-orange-400"
            >
              Go to Login
            </Link>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-semibold text-gray-200 transition hover:bg-white/10"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
