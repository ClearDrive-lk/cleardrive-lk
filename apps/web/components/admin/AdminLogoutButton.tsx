"use client";

import { Loader2, LogOut } from "lucide-react";

import { useLogout } from "@/lib/hooks/useLogout";

export default function AdminLogoutButton() {
  const { logout, isLoading } = useLogout();

  return (
    <button
      type="button"
      onClick={logout}
      disabled={isLoading}
      className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#393d3f] shadow-sm transition hover:bg-[#c6c5b9]/35 disabled:cursor-not-allowed disabled:opacity-70"
      aria-label="Sign out admin account"
    >
      {isLoading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Signing Out
        </>
      ) : (
        <>
          <LogOut className="h-4 w-4" />
          Sign Out
        </>
      )}
    </button>
  );
}
