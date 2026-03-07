"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";
import { ArrowLeft, Loader2 } from "lucide-react";
import apiClient from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const normalizedEmail = email.trim().toLowerCase();

  const handleRequestResetCode = async () => {
    if (!normalizedEmail) {
      setError("Email is required.");
      return;
    }

    try {
      setError(null);
      setStatusMessage(null);
      setRequesting(true);
      await apiClient.post("/auth/forgot-password", { email: normalizedEmail });
      setStatusMessage("If the email exists, a reset code has been sent.");
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string; message?: string }>;
      setError(
        axiosErr.response?.data?.detail ||
          axiosErr.response?.data?.message ||
          "Failed to request reset code. Please try again.",
      );
    } finally {
      setRequesting(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (
      !normalizedEmail ||
      !otp.trim() ||
      !newPassword.trim() ||
      !confirmPassword.trim()
    ) {
      setError("All fields are required.");
      return;
    }

    if (otp.trim().length !== 6 || !/^\d{6}$/.test(otp.trim())) {
      setError("OTP must be a 6-digit code.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setError(null);
      setStatusMessage(null);
      setResetting(true);
      await apiClient.post("/auth/reset-password", {
        email: normalizedEmail,
        otp: otp.trim(),
        new_password: newPassword,
      });
      setStatusMessage("Password reset successful. Redirecting to login...");
      setTimeout(() => router.push("/login"), 1000);
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string; message?: string }>;
      setError(
        axiosErr.response?.data?.detail ||
          axiosErr.response?.data?.message ||
          "Failed to reset password. Please try again.",
      );
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-[#0A0A0A] border border-white/10 p-8 rounded-2xl shadow-2xl">
        <Link
          href="/login"
          className="inline-flex items-center gap-2 text-xs text-gray-500 hover:text-white transition-colors mb-6"
        >
          <ArrowLeft className="w-3 h-3" />
          Back to Login
        </Link>

        <h1 className="text-2xl font-bold text-white mb-2">Reset Password</h1>
        <p className="text-sm text-gray-400 mb-6">
          Request a reset code, then submit the code with your new password.
        </p>

        <form onSubmit={handleResetPassword} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-xs text-gray-400 uppercase">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="bg-black/40 border-white/10 text-white"
            />
          </div>

          <Button
            type="button"
            onClick={handleRequestResetCode}
            disabled={requesting}
            variant="outline"
            className="w-full border-white/20 text-white hover:bg-white/10"
          >
            {requesting ? (
              <Loader2 className="animate-spin" />
            ) : (
              "Send Reset Code"
            )}
          </Button>

          <div className="space-y-2">
            <Label htmlFor="otp" className="text-xs text-gray-400 uppercase">
              OTP Code
            </Label>
            <Input
              id="otp"
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="6-digit code"
              inputMode="numeric"
              maxLength={6}
              required
              className="bg-black/40 border-white/10 text-white"
            />
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="new-password"
              className="text-xs text-gray-400 uppercase"
            >
              New Password
            </Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="bg-black/40 border-white/10 text-white"
            />
          </div>

          <div className="space-y-2">
            <Label
              htmlFor="confirm-password"
              className="text-xs text-gray-400 uppercase"
            >
              Confirm Password
            </Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="bg-black/40 border-white/10 text-white"
            />
          </div>

          {statusMessage && (
            <p className="text-sm text-green-400">{statusMessage}</p>
          )}
          {error && <p className="text-sm text-red-400">{error}</p>}

          <Button
            type="submit"
            disabled={resetting}
            className="w-full bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold"
          >
            {resetting ? (
              <Loader2 className="animate-spin" />
            ) : (
              "Reset Password"
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
