"use client";

import { useEffect, useState } from "react";
import { useAppSelector, useAppDispatch } from "@/lib/store/store";
import { setCredentials } from "@/lib/store/features/auth/authSlice";
import { useRouter, usePathname } from "next/navigation";
import {
  getAccessToken,
  getPersistAccessPreference,
  getRefreshToken,
  removeTokens,
  saveTokens,
} from "@/lib/auth";

/**
 * AuthGuard Component
 * Silent check - no "Checking authentication..." message
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let isCancelled = false;
    const checkAuth = async () => {
      // 1. If Redux says we are authenticated, we are good
      if (isAuthenticated) {
        if (!isCancelled) {
          setIsChecking(false);
        }
        return;
      }

      const accessToken = getAccessToken();
      const refreshToken = getRefreshToken();

      try {
        const baseUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

        if (accessToken) {
          const statusResponse = await fetch(`${baseUrl}/auth/status`, {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          });

          if (statusResponse.ok) {
            const data = (await statusResponse.json()) as {
              authenticated: boolean;
              user: { id: string; email: string; name: string; role: string };
            };

            const isAdmin = data.user.role?.toLowerCase() === "admin";
            dispatch(
              setCredentials({
                user: {
                  id: data.user.id,
                  email: data.user.email,
                  name: data.user.name || "User",
                  role: isAdmin ? "admin" : "user",
                },
                token: accessToken,
              }),
            );

            if (isAdmin && pathname.startsWith("/dashboard")) {
              router.replace("/admin/dashboard");
              return;
            }

            if (!isCancelled) {
              setIsChecking(false);
            }
            return;
          }
        }

        if (!refreshToken) {
          router.push("/login");
          return;
        }

        const response = await fetch(`${baseUrl}/auth/refresh`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
          throw new Error("Session refresh failed");
        }

        const data = (await response.json()) as {
          access_token: string;
          refresh_token: string;
          user: { id: string; email: string; name: string; role: string };
        };

        saveTokens(
          {
            access_token: data.access_token,
            refresh_token: data.refresh_token,
          },
          { persistAccess: getPersistAccessPreference() },
        );

        const isAdmin = data.user.role?.toLowerCase() === "admin";
        dispatch(
          setCredentials({
            user: {
              id: data.user.id,
              email: data.user.email,
              name: data.user.name || "User",
              role: isAdmin ? "admin" : "user",
            },
            token: data.access_token,
          }),
        );

        if (isAdmin && pathname.startsWith("/dashboard")) {
          router.replace("/admin/dashboard");
          return;
        }
      } catch {
        removeTokens();
        router.push("/login");
      } finally {
        if (!isCancelled) {
          setIsChecking(false);
        }
      }
    };

    void checkAuth();

    return () => {
      isCancelled = true;
    };
  }, [isAuthenticated, dispatch, router, pathname]);

  // Don't render anything while checking to avoid flash
  if (isChecking) {
    return null;
  }

  return <>{children}</>;
}
