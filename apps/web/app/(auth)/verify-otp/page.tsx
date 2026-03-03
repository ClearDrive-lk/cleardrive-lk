"use client";

import { useState, useRef, Suspense, useMemo, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Loader2,
  ShieldCheck,
  ArrowRight,
  ArrowLeft,
  Zap,
  Lock,
  Key,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { useAppDispatch } from "@/lib/store/store";
import { setCredentials } from "@/lib/store/features/auth/authSlice";
import { saveTokens } from "@/lib/auth";
import apiClient from "@/lib/api-client";
import { AxiosError } from "axios";
function OTPForm() {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSeconds, setResendSeconds] = useState(30);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const router = useRouter();
  const dispatch = useAppDispatch();
  const searchParams = useSearchParams();
  const emailFromQuery = searchParams.get("email");
  const emailFromSession =
    typeof window !== "undefined" ? sessionStorage.getItem("otp_email") : null;
  const email = useMemo(
    () => emailFromQuery || emailFromSession || "cleardrivelk@gmail.com",
    [emailFromQuery, emailFromSession],
  );

  useEffect(() => {
    if (resendSeconds <= 0) return;
    const timer = setInterval(() => {
      setResendSeconds((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [resendSeconds]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    if (value && index < 5) inputRefs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0)
      inputRefs.current[index - 1]?.focus();
  };

  const handlePaste = (
    index: number,
    e: React.ClipboardEvent<HTMLInputElement>,
  ) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "");
    if (!pasted) return;

    const nextOtp = [...otp];
    let cursor = index;

    for (const digit of pasted) {
      if (cursor > 5) break;
      nextOtp[cursor] = digit;
      cursor += 1;
    }

    setOtp(nextOtp);

    const focusIndex = Math.min(cursor, 5);
    inputRefs.current[focusIndex]?.focus();
  };

  const handleVerify = async () => {
    const otpCode = otp.join("");
    if (otpCode.length !== 6) return;

    try {
      setLoading(true);
      setError(null);
      setStatusMessage(null);

      const { data } = await apiClient.post<{
        access_token: string;
        refresh_token: string;
        user: {
          id: string;
          email: string;
          name: string;
          role: string;
        };
      }>("/auth/verify-otp", {
        email,
        otp: otpCode,
      });

      setSuccess(true);
      saveTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });

      dispatch(
        setCredentials({
          user: {
            id: data.user.id,
            email: data.user.email,
            name: data.user.name || "User",
            role: data.user.role?.toLowerCase() === "admin" ? "admin" : "user",
          },
          token: data.access_token,
        }),
      );

      if (typeof window !== "undefined") {
        sessionStorage.removeItem("otp_email");
      }

      setTimeout(() => router.push("/dashboard"), 800);
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string; message?: string }>;
      setError(
        axiosErr.response?.data?.detail ||
          axiosErr.response?.data?.message ||
          "OTP verification failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (resendSeconds > 0 || resendLoading) return;
    try {
      setResendLoading(true);
      setError(null);
      setStatusMessage(null);
      await apiClient.post("/auth/resend-otp", { email });
      setStatusMessage("A new OTP has been sent.");
      setResendSeconds(30);
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string; message?: string }>;
      setError(
        axiosErr.response?.data?.detail ||
          axiosErr.response?.data?.message ||
          "Failed to resend OTP. Please try again.",
      );
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex bg-[#050505] relative overflow-hidden font-sans selection:bg-[#FE7743] selection:text-black">
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 z-10 border-r border-white/5">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
          <div className="absolute top-[20%] left-[20%] w-[600px] h-[600px] bg-[#FE7743]/5 rounded-full blur-[120px]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        </div>
        <div className="relative z-10">
          <h1 className="text-2xl font-bold text-white tracking-tighter flex items-center gap-2">
            <ShieldCheck className="text-[#FE7743]" />
            Security Gateway
          </h1>
          <Badge
            variant="outline"
            className="mt-2 border-green-900/50 text-green-500 bg-green-900/10"
          >
            ENCRYPTED CONNECTION
          </Badge>
        </div>

        <div className="relative z-10 space-y-6 max-w-lg">
          <h2 className="text-4xl font-bold text-white leading-tight">
            Banking-Grade <br />
            Identity Verification.
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-gray-400 group">
              <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-[#FE7743] border border-white/10 group-hover:bg-[#FE7743]/10 transition-colors">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <p className="text-white font-medium">Instant Validation</p>
                <p className="text-xs">Code sent via SMS/Email Gateway</p>
              </div>
            </div>
            <div className="flex items-center gap-3 text-gray-400 group">
              <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-[#FE7743] border border-white/10 group-hover:bg-[#FE7743]/10 transition-colors">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-white font-medium">Session Protection</p>
                <p className="text-xs">
                  Prevents unauthorized account takeover
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-gray-600 font-mono">
          ID: AUTH-8829-XJ // 256-BIT ENCRYPTION
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative z-10">
        {/* Floating Back Button */}
        <div className="absolute top-8 left-8 z-20">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors group"
          >
            <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-[#FE7743]/10 group-hover:text-[#FE7743] transition-all">
              <ArrowLeft className="w-4 h-4" />
            </div>
            <span className="font-mono hidden sm:inline-block">
              RETURN HOME
            </span>
          </Link>
        </div>

        <div className="w-full max-w-md bg-[#0A0A0A] border border-white/10 p-8 rounded-2xl shadow-2xl relative z-10">
          <div className="mb-8 text-center">
            <div className="mx-auto w-16 h-16 bg-[#FE7743]/10 rounded-full flex items-center justify-center mb-6 border border-[#FE7743]/20 relative">
              <div className="absolute inset-0 bg-[#FE7743]/20 blur-md rounded-full animate-pulse" />
              {success ? (
                <CheckCircle2 className="text-green-500 w-8 h-8 relative z-10" />
              ) : (
                <Key className="text-[#FE7743] w-8 h-8 relative z-10" />
              )}
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">
              Two-Factor Authentication
            </h3>
            <p className="text-gray-400 text-sm">
              Enter the 6-digit security code sent to <br />
              <span className="text-[#FE7743] font-mono">{email}</span>
            </p>
          </div>

          <div className="space-y-8">
            <div className="flex gap-2 justify-center">
              {otp.map((digit, index) => (
                <Input
                  key={index}
                  ref={(el) => {
                    inputRefs.current[index] = el;
                  }}
                  type="text"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onPaste={(e) => handlePaste(index, e)}
                  className="w-12 h-14 text-center text-xl bg-black/40 border-white/10 focus:border-[#FE7743] focus:ring-[#FE7743]/20 transition-all text-white font-mono rounded-lg"
                />
              ))}
            </div>

            <Button
              onClick={handleVerify}
              disabled={loading || otp.some((d) => !d) || success}
              className={`w-full font-bold h-12 transition-all shadow-lg ${
                success
                  ? "bg-green-500 hover:bg-green-600 text-black"
                  : "bg-[#FE7743] hover:bg-[#FE7743]/90 text-black shadow-[0_0_15px_rgba(254,119,67,0.15)]"
              }`}
            >
              {loading ? (
                <Loader2 className="animate-spin" />
              ) : success ? (
                "Access Granted"
              ) : (
                "Verify & Access Terminal"
              )}
            </Button>

            <div className="text-center text-xs text-gray-500 font-mono">
              Didn&apos;t receive code?{" "}
              <button
                onClick={handleResend}
                disabled={resendSeconds > 0 || resendLoading}
                className="hover:text-white disabled:text-gray-600 disabled:no-underline transition-colors underline decoration-[#FE7743]"
              >
                {resendLoading
                  ? "Resending..."
                  : resendSeconds > 0
                    ? `Resend in ${resendSeconds}s`
                    : "Resend now"}
              </button>
            </div>
            {statusMessage && (
              <p className="text-center text-xs text-green-400 font-mono">
                {statusMessage}
              </p>
            )}
            {error && (
              <p className="text-center text-xs text-red-400 font-mono">
                {error}
              </p>
            )}
          </div>

          <div className="mt-8 pt-6 border-t border-white/5 text-center">
            <Link
              href="/login"
              className="text-xs text-gray-400 hover:text-white flex items-center justify-center gap-2 group"
            >
              <ArrowRight className="w-3 h-3 rotate-180 group-hover:-translate-x-1 transition-transform" />
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OTPPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
          Loading Security Gateway...
        </div>
      }
    >
      <OTPForm />
    </Suspense>
  );
}
