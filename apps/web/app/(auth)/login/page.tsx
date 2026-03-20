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
  ShieldAlert,
  ArrowLeft,
  Eye,
  EyeOff,
  Mail,
  Radar,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import apiClient from "@/lib/api-client";
import { AxiosError } from "axios";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import ThemeToggle from "@/components/ui/theme-toggle";

const SECURITY_CONTROLS = [
  {
    gate: "GATE 01",
    title: "Credential Integrity",
    summary: "Password validation starts the flow.",
    detail:
      "Email and password are verified first, but this gate alone cannot create a session.",
    proof: "Uniform failure responses reduce account-enumeration leakage.",
    icon: Lock,
  },
  {
    gate: "GATE 02",
    title: "One-Time Email Proof",
    summary: "Second factor is mandatory.",
    detail:
      "A one-time verification code is sent and must be confirmed before any access token is issued.",
    proof: "Login is a two-step handshake: credentials, then OTP verification.",
    icon: Mail,
  },
  {
    gate: "GATE 03",
    title: "Brute-Force Throttle",
    summary: "Replay and guessing are constrained.",
    detail:
      "Verification attempts are capped and rate-limited to block rapid OTP abuse patterns.",
    proof: "OTP attempts are limited to 3 with additional rate-limit controls.",
    icon: ShieldAlert,
  },
  {
    gate: "GATE 04",
    title: "Session Risk Scan",
    summary: "Anomalous sign-ins are flagged.",
    detail:
      "Session metadata and suspicious-activity checks run in the verification pipeline before finalizing access.",
    proof: "Risk signaling is wired into OTP verification and session creation flow.",
    icon: Radar,
  },
] as const;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [activeSecurityGate, setActiveSecurityGate] = useState(0);
  const [securitySpotlight, setSecuritySpotlight] = useState({ x: 50, y: 32 });
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

  const handleSecurityMatrixMove = (event: React.MouseEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    setSecuritySpotlight({ x, y });
  };

  const resetSecurityMatrixSpotlight = () => {
    setSecuritySpotlight({ x: 50, y: 32 });
  };

  const activeGate = SECURITY_CONTROLS[activeSecurityGate];

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
            <BrandMark className="h-11 w-11" />
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

        <div className="relative z-10 max-w-2xl space-y-6">
          <div className="space-y-3">
            <p className="inline-flex items-center gap-2 rounded-full border border-[#62929e]/25 bg-[#62929e]/10 px-3 py-1 text-[10px] font-mono uppercase tracking-[0.24em] text-[#62929e]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#62929e] animate-pulse" />
              Adaptive Security Matrix
            </p>
            <h2 className="text-5xl font-bold text-[#393d3f] leading-tight tracking-tight">
              Four Security Gates. <br />
              One Controlled Session.
            </h2>
            <p className="max-w-xl text-sm leading-relaxed text-[#546a7b]">
              Move across the matrix to inspect how each login request is
              hardened before access is granted. This is not decoration. These
              checks define the actual sign-in pipeline.
            </p>
          </div>

          <section
            className="relative overflow-hidden rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/10 p-5 backdrop-blur-xl"
            onMouseMove={handleSecurityMatrixMove}
            onMouseLeave={resetSecurityMatrixSpotlight}
          >
            <div
              className="pointer-events-none absolute -inset-16 opacity-90 transition-[background] duration-200"
              style={{
                background: `radial-gradient(360px circle at ${securitySpotlight.x}% ${securitySpotlight.y}%, rgba(98,146,158,0.32), rgba(98,146,158,0) 65%)`,
              }}
            />

            <div className="pointer-events-none absolute right-5 top-5 h-16 w-16">
              <div className="absolute inset-0 rounded-full border border-[#62929e]/35 animate-ping [animation-duration:2.8s]" />
              <div className="absolute inset-[10px] rounded-full border border-[#62929e]/45" />
              <div className="absolute inset-[22px] rounded-full bg-[#62929e]/55" />
            </div>

            <div className="relative grid grid-cols-2 gap-3">
              {SECURITY_CONTROLS.map((gate, index) => {
                const Icon = gate.icon;
                const isActive = index === activeSecurityGate;

                return (
                  <button
                    key={gate.gate}
                    type="button"
                    onMouseEnter={() => setActiveSecurityGate(index)}
                    onFocus={() => setActiveSecurityGate(index)}
                    className={`rounded-xl border p-3 text-left transition-all duration-200 ${
                      isActive
                        ? "border-[#62929e]/60 bg-[#62929e]/16 shadow-[0_12px_24px_rgba(98,146,158,0.24)]"
                        : "border-[#546a7b]/50 bg-[#fdfdff]/8 hover:border-[#62929e]/45 hover:bg-[#62929e]/10"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-[#62929e]">
                        {gate.gate}
                      </span>
                      <Icon className="h-4 w-4 text-[#62929e]" />
                    </div>
                    <p className="mt-2 text-sm font-semibold text-[#393d3f]">
                      {gate.title}
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-[#546a7b]">
                      {gate.summary}
                    </p>
                  </button>
                );
              })}
            </div>

            <div className="relative mt-4 rounded-xl border border-[#546a7b]/55 bg-[#fdfdff]/14 p-4">
              <div className="flex items-center justify-between gap-4">
                <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[#62929e]">
                  Active Inspection
                </p>
                <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[#546a7b]">
                  {activeGate.gate}
                </span>
              </div>
              <h3 className="mt-1 text-lg font-bold text-[#393d3f]">
                {activeGate.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-[#546a7b]">
                {activeGate.detail}
              </p>
              <p className="mt-3 text-[11px] font-mono uppercase tracking-[0.13em] text-[#62929e]">
                {activeGate.proof}
              </p>
              <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-[#546a7b]/20">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#62929e] to-[#c6c5b9] transition-all duration-300"
                  style={{
                    width: `${((activeSecurityGate + 1) / SECURITY_CONTROLS.length) * 100}%`,
                  }}
                />
              </div>
            </div>
          </section>
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
        <div className="absolute top-8 right-8 z-20">
          <ThemeToggle />
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
              <div className="relative">
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
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#546a7b] hover:text-[#393d3f] transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
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
