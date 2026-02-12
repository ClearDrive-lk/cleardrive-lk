"use client";

<<<<<<< HEAD
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
=======
import { useState } from "react";
import { useRouter } from "next/navigation"; // Import Router
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
import Link from "next/link";
import { GoogleLoginButton } from "@/components/auth/GoogleLoginButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
<<<<<<< HEAD
import { Loader2, Lock, ShieldCheck, Terminal, ArrowLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // --- AUTO-CLEANUP: Log out user when they visit Login Page ---
  useEffect(() => {
    // This ensures we start with a clean state every time
    // Clear tokens matching new auth strategy
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("access_token");
      document.cookie = "refresh_token=; path=/; Max-Age=0";
    }
  }, []);
=======
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter(); // Initialize Router
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98

  const handleEmailLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
<<<<<<< HEAD

    // --- STEP 1: AUTHENTICATION CHECK ---
    // We do NOT set the cookie here. We pass the user to the Security Gateway (OTP).
    setTimeout(() => {
      setLoading(false);
      // Redirect to OTP Page with a fake email param for the UI
      router.push("/verify-otp?email=agent@cleardrive.lk");
    }, 1500);
  };

  return (
    <div className="min-h-screen w-full flex bg-[#050505] relative overflow-hidden font-sans selection:bg-[#FE7743] selection:text-black">
      {/* --- VISUAL SIDE (LEFT) - The "Terminal" Aesthetic --- */}
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 z-10 border-r border-white/5">
        {/* Animated Background Layers */}
=======
    // Email/password login not implemented yet — use Google to sign in
    setTimeout(() => {
      setLoading(false);
      alert('Please use "Continue with Google" to sign in.');
    }, 300);
  };

  return (
    <div className="min-h-screen w-full flex bg-[#050505] relative overflow-hidden font-sans">
      {/* --- VISUAL SIDE (LEFT) --- */}
      <div className="hidden lg:flex w-1/2 relative flex-col justify-between p-12 z-10">
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
          <div className="absolute top-[-20%] left-[-20%] w-[800px] h-[800px] bg-[#FE7743]/10 rounded-full blur-[120px]" />
          <div className="absolute bottom-[-20%] right-[-20%] w-[600px] h-[600px] bg-[#273F4F]/20 rounded-full blur-[100px]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
        </div>

        <div className="relative z-10">
<<<<<<< HEAD
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
=======
          <h1 className="text-4xl font-bold text-white tracking-tighter">
            ClearDrive<span className="text-[#FE7743]">.lk</span>
          </h1>
          <p className="text-gray-400 mt-2 text-sm uppercase tracking-widest font-mono">
            Direct Market Access Terminal v1.0
          </p>
        </div>

        <div className="relative z-10 space-y-6 max-w-lg">
          <h2 className="text-5xl font-bold text-white leading-tight">
            Import Vehicles <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
              Without The Middleman.
            </span>
          </h2>
          <p className="text-gray-400 text-lg leading-relaxed">
            Access real-time JPY auction data, calculate landed costs instantly,
            and secure your vehicle with blockchain-verified transparency.
          </p>
        </div>

        <div className="relative z-10 text-xs text-gray-600 font-mono">
          © 2026 CLEARDRIVE INC. // SECURE CONNECTION ESTABLISHED
        </div>
      </div>

      {/* --- FORM SIDE (RIGHT) --- */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 relative z-10">
        <div className="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-2xl shadow-2xl relative z-10">
          <div className="mb-8 text-center lg:text-left">
            <h3 className="text-2xl font-bold text-white mb-2">Welcome Back</h3>
            <p className="text-gray-400 text-sm">
              Enter your credentials to access the terminal.
            </p>
          </div>

          <form onSubmit={handleEmailLogin} className="space-y-4">
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
            <div className="space-y-2">
              <Label
                htmlFor="email"
                className="text-xs font-mono text-gray-400 uppercase"
              >
<<<<<<< HEAD
                Agent ID / Email
=======
                Email Address
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
              </Label>
              <Input
                id="email"
                placeholder="agent@cleardrive.lk"
                type="email"
<<<<<<< HEAD
                className="bg-black/40 border-white/10 text-white placeholder:text-gray-700 focus:border-[#FE7743] focus:ring-1 focus:ring-[#FE7743]/50 h-12 font-mono transition-all"
              />
            </div>

=======
                className="bg-black/40 border-white/10 text-white placeholder:text-gray-600 focus:border-[#FE7743] h-11"
              />
            </div>
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label
                  htmlFor="password"
                  className="text-xs font-mono text-gray-400 uppercase"
                >
<<<<<<< HEAD
                  Access Key
                </Label>
                <Link
                  href="#"
                  className="text-xs text-[#FE7743] hover:text-[#FE7743]/80 transition-colors"
                >
                  Lost Key?
=======
                  Password
                </Label>
                <Link
                  href="#"
                  className="text-xs text-[#FE7743] hover:text-[#FE7743]/80"
                >
                  Forgot?
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
                </Link>
              </div>
              <Input
                id="password"
                type="password"
<<<<<<< HEAD
                className="bg-black/40 border-white/10 text-white focus:border-[#FE7743] focus:ring-1 focus:ring-[#FE7743]/50 h-12 font-mono tracking-widest transition-all"
              />
            </div>

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
=======
                className="bg-black/40 border-white/10 text-white focus:border-[#FE7743] h-11"
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold h-11"
            >
              {loading ? <Loader2 className="animate-spin" /> : "Sign In"}
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
            </Button>
          </form>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/10"></span>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
<<<<<<< HEAD
              <span className="bg-[#0A0A0A] px-2 text-gray-500 font-mono">
                Or connect with
=======
              <span className="bg-[#0A0A0A]/50 backdrop-blur px-2 text-gray-500">
                Or continue with
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
              </span>
            </div>
          </div>

<<<<<<< HEAD
          <div className="w-full grayscale hover:grayscale-0 transition-all duration-300">
            <GoogleLoginButton />
          </div>

          <div className="mt-8 pt-6 border-t border-white/5 text-center text-sm text-gray-500">
            New Dealer?{" "}
=======
          <div className="w-full">
            <GoogleLoginButton />
          </div>
          <div className="mt-8 text-center text-sm text-gray-500">
            Don&apos;t have an account?{" "}
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
            <Link
              href="/register"
              className="text-white hover:text-[#FE7743] font-medium transition-colors"
            >
<<<<<<< HEAD
              Request API Access
=======
              Request Access
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
