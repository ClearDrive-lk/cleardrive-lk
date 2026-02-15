"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Terminal, ArrowLeft, Loader2, Eye, EyeOff } from "lucide-react";
import apiClient from "@/lib/api-client";
import { AxiosError } from "axios";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedEmail || !password.trim() || !confirmPassword.trim()) {
      setError("Email and password fields are required.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await apiClient
        .post("/auth/dev/ensure-user", { email: normalizedEmail })
        .catch(() => undefined);
      await apiClient.post("/auth/request-otp", { email: normalizedEmail });

      if (typeof window !== "undefined") {
        sessionStorage.setItem("otp_email", normalizedEmail);
      }
      setLoading(false);
      router.push(`/verify-otp?email=${encodeURIComponent(normalizedEmail)}`);
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string; message?: string }>;
      setError(
        axiosErr.response?.data?.detail ||
          axiosErr.response?.data?.message ||
          "Failed to send OTP. Please try again.",
      );
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#050505] relative overflow-hidden font-sans selection:bg-[#FE7743] selection:text-black p-6">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
      <div className="absolute top-[20%] right-[20%] w-[600px] h-[600px] bg-[#FE7743]/5 rounded-full blur-[120px]" />

      <div className="w-full max-w-md bg-[#0A0A0A] border border-white/10 p-8 rounded-2xl shadow-2xl relative z-10">
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs text-gray-500 hover:text-white transition-colors font-mono mb-6"
          >
            <ArrowLeft className="w-3 h-3" />
            RETURN HOME
          </Link>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Terminal className="w-5 h-5 text-[#FE7743]" />
            Create Account
          </h1>
          <p className="text-sm text-gray-400 mt-2">
            Enter your email and password to start registration.
          </p>
        </div>

        <form onSubmit={handleRegister} className="space-y-5">
          <div className="space-y-2">
            <Label
              htmlFor="email"
              className="text-xs font-mono text-gray-400 uppercase"
            >
              Dealer Email
            </Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="dealer@company.com"
              required
              className="bg-black/40 border-white/10 text-white placeholder:text-gray-700 focus:border-[#FE7743] focus:ring-1 focus:ring-[#FE7743]/50 h-12 font-mono transition-all"
            />
          </div>

          <div className="space-y-2 relative">
            <Label
              htmlFor="password"
              className="text-xs font-mono text-gray-400 uppercase"
            >
              Password
            </Label>
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="bg-black/40 border-white/10 text-white focus:border-[#FE7743] focus:ring-1 focus:ring-[#FE7743]/50 h-12 font-mono transition-all pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-[38px] text-gray-500 hover:text-white transition-colors"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>

          <div className="space-y-2 relative">
            <Label
              htmlFor="confirm-password"
              className="text-xs font-mono text-gray-400 uppercase"
            >
              Confirm Password
            </Label>
            <Input
              id="confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="bg-black/40 border-white/10 text-white focus:border-[#FE7743] focus:ring-1 focus:ring-[#FE7743]/50 h-12 font-mono transition-all pr-12"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword((v) => !v)}
              className="absolute right-3 top-[38px] text-gray-500 hover:text-white transition-colors"
              aria-label={
                showConfirmPassword
                  ? "Hide confirm password"
                  : "Show confirm password"
              }
            >
              {showConfirmPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold h-12"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Continue to OTP"}
          </Button>
        </form>

        <div className="mt-8 pt-6 border-t border-white/5 text-center text-sm text-gray-500">
          Already registered?{" "}
          <Link
            href="/login"
            className="text-white hover:text-[#FE7743] font-medium transition-colors"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
