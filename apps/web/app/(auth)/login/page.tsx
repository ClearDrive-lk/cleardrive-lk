"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GoogleLoginButton } from "@/components/auth/GoogleLoginButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Loader2,
  Lock,
  ShieldCheck,
  ArrowLeft,
  Eye,
  EyeOff,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import apiClient from "@/lib/api-client";
import { AxiosError } from "axios";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  // Do not auto-clear tokens on login page.

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    const trimmedPassword = password.trim();
    if (!normalizedEmail || !trimmedPassword) {
      setError("Email and password are required.");
      return;
    }

    try {
      setError(null);
      setLoading(true);

      await apiClient.post("/auth/login", {
        email: normalizedEmail,
        password: trimmedPassword,
      });

      setLoading(false);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("otp_email", normalizedEmail);
      }
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
    <div className="min-h-screen w-full flex bg-[#fdfdff] relative overflow-hidden font-sans selection:bg-[#62929e] selection:text-[#fdfdff]">
      {/* --- VISUAL SIDE (LEFT) - The "Terminal" Aesthetic --- */}
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 z-10 border-r border-[#546a7b]/40">
        {/* Animated Background Layers */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
          <div className="absolute top-[-20%] left-[-20%] w-[800px] h-[800px] bg-[#62929e]/10 rounded-full blur-[120px]" />
          <div className="absolute bottom-[-20%] right-[-20%] w-[600px] h-[600px] bg-[#c6c5b9]/40 rounded-full blur-[100px]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px]" />
        </div>

        <div className="relative z-10">
          <div className="font-bold text-2xl tracking-tighter flex items-center gap-2 text-[#393d3f]">
            <BrandMark className="h-7 w-7 rounded-md border border-[#62929e]/20 bg-[#62929e]/10" />
            <BrandWordmark />
          </div>
          <div className="mt-4 flex gap-2">
            <Badge
              variant="outline"
              className="border-[#62929e]/20 text-[#62929e] bg-[#62929e]/5 flex items-center gap-1"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#62929e] animate-pulse" />
              SYSTEM ONLINE
            </Badge>
            <Badge
              variant="outline"
              className="border-[#546a7b]/65 text-[#546a7b]"
            >
              v2.4.0-stable
            </Badge>
          </div>
        </div>

        <div className="relative z-10 space-y-8 max-w-lg">
          <h2 className="text-5xl font-bold text-[#393d3f] leading-tight tracking-tight">
            Authorized <br />
            Personnel Only.
          </h2>
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 rounded-lg bg-[#c6c5b9]/20 border border-[#546a7b]/65 backdrop-blur-md hover:bg-[#c6c5b9]/30 transition-colors">
              <ShieldCheck className="w-6 h-6 text-[#62929e] mt-1" />
              <div>
                <h3 className="font-bold text-[#393d3f]">
                  Direct Market Access
                </h3>
                <p className="text-sm text-[#546a7b] mt-1">
                  Secure gateway to USS Tokyo & JAA live auction data with
                  sub-millisecond latency.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-lg bg-[#c6c5b9]/20 border border-[#546a7b]/65 backdrop-blur-md hover:bg-[#c6c5b9]/30 transition-colors">
              <Lock className="w-6 h-6 text-[#62929e] mt-1" />
              <div>
                <h3 className="font-bold text-[#393d3f]">
                  End-to-End Encryption
                </h3>
                <p className="text-sm text-[#546a7b] mt-1">
                  Financial data and bidding instructions are protected by
                  AES-256 GCM encryption.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-[#393d3f] font-mono flex justify-between items-center border-t border-[#546a7b]/40 pt-6">
          <span>IP: 192.168.1.X // CLIENT: WEB_TERMINAL</span>
          <span>SESSION ID: AUTH-8829-XJ</span>
        </div>
      </div>

      {/* --- FORM SIDE (RIGHT) - The "Login" Interface --- */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative z-10">
        {/* Mobile Background Blob */}
        <div className="lg:hidden absolute inset-0 z-0">
          <div className="absolute top-[20%] right-[-10%] w-64 h-64 bg-[#62929e]/10 rounded-full blur-[80px]" />
        </div>

        {/* Floating Back Button */}
        <div className="absolute top-8 left-8 z-20">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm text-[#546a7b] hover:text-[#393d3f] transition-colors group"
          >
            <div className="w-8 h-8 rounded-full bg-[#c6c5b9]/20 flex items-center justify-center group-hover:bg-[#62929e]/10 group-hover:text-[#62929e] transition-all">
              <ArrowLeft className="w-4 h-4" />
            </div>
            <span className="font-mono hidden sm:inline-block">
              RETURN HOME
            </span>
          </Link>
        </div>

        <div className="w-full max-w-md bg-[#fdfdff] border border-[#546a7b]/65 p-8 rounded-2xl shadow-2xl relative z-10">
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-[#393d3f] mb-2">
              Terminal Access
            </h3>
            <p className="text-[#546a7b] text-sm">
              Please identify yourself to proceed.
            </p>
          </div>

          <form onSubmit={handleEmailLogin} className="space-y-5">
            <div className="space-y-2 relative">
              <Label
                htmlFor="email"
                className="text-xs font-mono text-[#546a7b] uppercase"
              >
                Agent ID / Email
              </Label>
              <Input
                id="email"
                placeholder="cleardrivelk@gmail.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-[#fdfdff]/40 border-[#546a7b]/65 text-[#393d3f] placeholder:text-gray-700 focus:border-[#62929e] focus:ring-1 focus:ring-[#62929e]/50 h-12 font-mono transition-all"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label
                  htmlFor="password"
                  className="text-xs font-mono text-[#546a7b] uppercase"
                >
                  Access Key
                </Label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-[#62929e] hover:text-[#62929e]/80 transition-colors"
                >
                  Lost Key?
                </Link>
              </div>
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-[#fdfdff]/40 border-[#546a7b]/65 text-[#393d3f] focus:border-[#62929e] focus:ring-1 focus:ring-[#62929e]/50 h-12 font-mono tracking-widest transition-all pr-12"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-[38px] text-[#546a7b] hover:text-[#393d3f] transition-colors"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
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
              className="w-full bg-[#62929e] hover:bg-[#62929e]/90 text-[#fdfdff] font-bold h-12 text-md transition-all shadow-[0_0_20px_rgba(98,146,158,0.2)] hover:shadow-[0_0_30px_rgba(98,146,158,0.4)]"
            >
              {loading ? (
                <Loader2 className="animate-spin" />
              ) : (
                "Authenticate Session"
              )}
            </Button>
          </form>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-[#546a7b]/65"></span>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[#fdfdff] px-2 text-[#546a7b] font-mono">
                Or connect with
              </span>
            </div>
          </div>

          <div className="w-full grayscale hover:grayscale-0 transition-all duration-300">
            <GoogleLoginButton />
          </div>

          <div className="mt-8 pt-6 border-t border-[#546a7b]/40 text-center text-sm text-[#546a7b]">
            New customer?{" "}
            <Link
              href="/register"
              className="text-[#393d3f] hover:text-[#62929e] font-medium transition-colors"
            >
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
