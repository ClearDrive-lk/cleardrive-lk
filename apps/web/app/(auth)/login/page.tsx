"use client";

import { useState, useEffect } from "react";
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
  Terminal,
  ArrowLeft,
  Eye,
  EyeOff,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { removeTokens } from "@/lib/auth";
import apiClient from "@/lib/api-client";
import { AxiosError } from "axios";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  // --- AUTO-CLEANUP: Log out user when they visit Login Page ---
  useEffect(() => {
    // This ensures we start with a clean state every time
    removeTokens();
  }, []);

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password.trim()) {
      setError("Email and password are required.");
      return;
    }

    try {
      setError(null);
      setLoading(true);

      // Dev convenience: ensure user exists when backend supports this endpoint.
      await apiClient
        .post("/auth/dev/ensure-user", { email: normalizedEmail })
        .catch(() => undefined);

      await apiClient.post("/auth/request-otp", { email: normalizedEmail });

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
    <div className="min-h-screen w-full flex bg-[#050505] relative overflow-hidden font-sans selection:bg-[#FE7743] selection:text-black">
      {/* --- VISUAL SIDE (LEFT) - The "Terminal" Aesthetic --- */}
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 z-10 border-r border-white/5">
        {/* Animated Background Layers */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
          <div className="absolute top-[-20%] left-[-20%] w-[800px] h-[800px] bg-[#FE7743]/10 rounded-full blur-[120px]" />
          <div className="absolute bottom-[-20%] right-[-20%] w-[600px] h-[600px] bg-[#273F4F]/20 rounded-full blur-[100px]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        </div>

        <div className="relative z-10">
          <div className="font-bold text-2xl tracking-tighter flex items-center gap-2 text-white">
            <Terminal className="w-6 h-6 text-[#FE7743]" />
            ClearDrive<span className="text-[#FE7743]">.lk</span>
          </div>
          <div className="mt-4 flex gap-2">
            <Badge
              variant="outline"
              className="border-[#FE7743]/20 text-[#FE7743] bg-[#FE7743]/5 flex items-center gap-1"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#FE7743] animate-pulse" />
              SYSTEM ONLINE
            </Badge>
            <Badge variant="outline" className="border-white/10 text-gray-500">
              v2.4.0-stable
            </Badge>
          </div>
        </div>

        <div className="relative z-10 space-y-8 max-w-lg">
          <h2 className="text-5xl font-bold text-white leading-tight tracking-tight">
            Authorized <br />
            Personnel Only.
          </h2>
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md hover:bg-white/10 transition-colors">
              <ShieldCheck className="w-6 h-6 text-[#FE7743] mt-1" />
              <div>
                <h3 className="font-bold text-white">Direct Market Access</h3>
                <p className="text-sm text-gray-400 mt-1">
                  Secure gateway to USS Tokyo & JAA live auction data with
                  sub-millisecond latency.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md hover:bg-white/10 transition-colors">
              <Lock className="w-6 h-6 text-[#FE7743] mt-1" />
              <div>
                <h3 className="font-bold text-white">End-to-End Encryption</h3>
                <p className="text-sm text-gray-400 mt-1">
                  Financial data and bidding instructions are protected by
                  AES-256 GCM encryption.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-gray-600 font-mono flex justify-between items-center border-t border-white/5 pt-6">
          <span>IP: 192.168.1.X // CLIENT: WEB_TERMINAL</span>
          <span>SESSION ID: AUTH-8829-XJ</span>
        </div>
      </div>

      {/* --- FORM SIDE (RIGHT) - The "Login" Interface --- */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative z-10">
        {/* Mobile Background Blob */}
        <div className="lg:hidden absolute inset-0 z-0">
          <div className="absolute top-[20%] right-[-10%] w-64 h-64 bg-[#FE7743]/10 rounded-full blur-[80px]" />
        </div>

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
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-white mb-2">
              Terminal Access
            </h3>
            <p className="text-gray-400 text-sm">
              Please identify yourself to proceed.
            </p>
          </div>

          <form onSubmit={handleEmailLogin} className="space-y-5">
            <div className="space-y-2 relative">
              <Label
                htmlFor="email"
                className="text-xs font-mono text-gray-400 uppercase"
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
                className="bg-black/40 border-white/10 text-white placeholder:text-gray-700 focus:border-[#FE7743] focus:ring-1 focus:ring-[#FE7743]/50 h-12 font-mono transition-all"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label
                  htmlFor="password"
                  className="text-xs font-mono text-gray-400 uppercase"
                >
                  Access Key
                </Label>
                <Link
                  href="#"
                  className="text-xs text-[#FE7743] hover:text-[#FE7743]/80 transition-colors"
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
                className="bg-black/40 border-white/10 text-white focus:border-[#FE7743] focus:ring-1 focus:ring-[#FE7743]/50 h-12 font-mono tracking-widest transition-all pr-12"
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

            {error && <p className="text-sm text-red-400">{error}</p>}

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold h-12 text-md transition-all shadow-[0_0_20px_rgba(254,119,67,0.2)] hover:shadow-[0_0_30px_rgba(254,119,67,0.4)]"
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
              <span className="w-full border-t border-white/10"></span>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[#0A0A0A] px-2 text-gray-500 font-mono">
                Or connect with
              </span>
            </div>
          </div>

          <div className="w-full grayscale hover:grayscale-0 transition-all duration-300">
            <GoogleLoginButton />
          </div>

          <div className="mt-8 pt-6 border-t border-white/5 text-center text-sm text-gray-500">
            New customer?{" "}
            <Link
              href="/register"
              className="text-white hover:text-[#FE7743] font-medium transition-colors"
            >
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
