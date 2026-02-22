"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { logout as logoutAction } from "@/lib/store/features/auth/authSlice";
import { useAppDispatch } from "@/lib/store/store";
import { removeTokens } from "@/lib/auth";
import apiClient from "@/lib/api-client";

export function useLogout() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const dispatch = useAppDispatch();

  const logout = async () => {
    if (isLoading) return;
    setIsLoading(true);

    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Continue with local logout even if backend logout fails.
    } finally {
      removeTokens();
      dispatch(logoutAction());
      setIsLoading(false);
      router.push("/login");
    }
  };

  return { logout, isLoading };
}
