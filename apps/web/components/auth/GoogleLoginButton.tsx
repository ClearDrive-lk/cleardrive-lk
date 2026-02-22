"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import apiClient from "@/lib/api-client";
import { AxiosError } from "axios";
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
            auto_select?: boolean;
          }) => void;
          prompt: (momentListener?: (value: unknown) => void) => void;
        };
      };
    };
  }
}

const GSI_SRC = "https://accounts.google.com/gsi/client";

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google script"));
    document.head.appendChild(script);
  });
}

export function GoogleLoginButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const clientId =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
      : undefined;

  const handleCredential = useCallback(
    async (idToken: string) => {
      if (!idToken) return;
      setLoading(true);
      setError(null);
      try {
        const { data } = await apiClient.post<{
          email: string;
          name?: string;
          google_id: string;
          message: string;
        }>("/auth/google", { id_token: idToken });
        if (data.email) {
          if (typeof window !== "undefined") {
            sessionStorage.setItem("otp_email", data.email);
          }
          router.push(`/verify-otp?email=${encodeURIComponent(data.email)}`);
          return;
        }
        setError("Invalid response from server");
      } catch (err: unknown) {
        const axiosErr = err as AxiosError<{
          detail?: string | { message?: string };
          message?: string;
        }>;
        const detail = axiosErr.response?.data?.detail;
        const msg =
          (typeof detail === "string" && detail) ||
          (typeof detail === "object" &&
            detail &&
            "message" in detail &&
            typeof detail.message === "string" &&
            detail.message) ||
          axiosErr.response?.data?.message ||
          axiosErr.message ||
          null;
        if (axiosErr.code === "ERR_NETWORK") {
          const apiBase =
            process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
          setError(
            `Cannot reach API server (${apiBase}). Start backend and try again.`,
          );
          return;
        }
        setError(
          typeof msg === "string" ? msg : "Google sign-in failed. Try again.",
        );
      } finally {
        setLoading(false);
      }
    },
    [router],
  );

  useEffect(() => {
    if (!clientId || typeof window === "undefined") return;
    loadScript(GSI_SRC)
      .then(() => {
        if (window.google?.accounts?.id) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: (response) => handleCredential(response.credential),
            auto_select: false,
          });
        }
      })
      .catch(() => setError("Could not load Google Sign-In"));
  }, [clientId, handleCredential]);

  const handleLogin = async () => {
    setError(null);
    if (!clientId) {
      setError(
        "Google Client ID not configured. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID.",
      );
      return;
    }
    if (typeof window === "undefined" || !window.google?.accounts?.id) {
      setError("Google Sign-In is still loading. Try again in a moment.");
      return;
    }
    setLoading(true);
    try {
      window.google.accounts.id.prompt((notification: unknown) => {
        const n = notification as {
          isNotDisplayed?: () => boolean;
          isSkippedMoment?: () => boolean;
          getNotDisplayedReason?: () => string;
          getSkippedReason?: () => string;
        };

        // FedCM can cancel prompt flow without this being an application error.
        // Clear loading state and only surface actionable prompt issues.
        setLoading(false);

        if (n?.isNotDisplayed?.()) {
          const reason = n.getNotDisplayedReason?.() || "unknown";
          setError(`Google sign-in prompt unavailable (${reason}).`);
          return;
        }

        if (n?.isSkippedMoment?.()) {
          const reason = n.getSkippedReason?.();
          if (reason && reason !== "user_cancel") {
            setError(`Google sign-in was skipped (${reason}).`);
          }
        }
      });
    } catch {
      setError("Google Sign-In failed");
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-2">
      <Button
        onClick={handleLogin}
        disabled={loading}
        variant="outline"
        className="w-full bg-white text-black hover:bg-gray-200 border-0 h-11 font-medium transition-all"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Connecting...
          </>
        ) : (
          <div className="flex items-center gap-3">
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </div>
        )}
      </Button>
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
