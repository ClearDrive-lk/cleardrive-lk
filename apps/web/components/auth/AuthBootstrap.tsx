"use client";

import { useEffect, useRef } from "react";
import { setCredentials } from "@/lib/store/features/auth/authSlice";
import { useAppDispatch, useAppSelector } from "@/lib/store/store";
import { getAccessToken, getRefreshToken, saveTokens } from "@/lib/auth";
import { normalizeRole } from "@/lib/roles";

export default function AuthBootstrap() {
  const dispatch = useAppDispatch();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current || isAuthenticated) return;
    hasRun.current = true;

    const run = async () => {
      const baseUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const accessToken = getAccessToken();
      const refreshToken = getRefreshToken();

      if (!accessToken && !refreshToken) return;

      try {
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
            dispatch(
              setCredentials({
                user: {
                  id: data.user.id,
                  email: data.user.email,
                  name: data.user.name || "User",
                  role: normalizeRole(data.user.role),
                },
                token: accessToken,
              }),
            );
            return;
          }
        }

        if (refreshToken) {
          const refreshResponse = await fetch(`${baseUrl}/auth/refresh`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (!refreshResponse.ok) return;

          const data = (await refreshResponse.json()) as {
            access_token: string;
            refresh_token: string;
            user: { id: string; email: string; name: string; role: string };
          };

          saveTokens(
            {
              access_token: data.access_token,
              refresh_token: data.refresh_token,
            },
            { persistAccess: true },
          );

          dispatch(
            setCredentials({
              user: {
                id: data.user.id,
                email: data.user.email,
                name: data.user.name || "User",
                role: normalizeRole(data.user.role),
              },
              token: data.access_token,
            }),
          );
        }
      } catch {
        // Silent bootstrap failure. AuthGuard handles redirect on protected pages.
      }
    };

    void run();
  }, [dispatch, isAuthenticated]);

  return null;
}
