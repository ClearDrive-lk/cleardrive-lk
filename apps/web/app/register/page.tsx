"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Terminal, Construction, ArrowLeft } from "lucide-react";

export default function RegisterPage() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#050505] relative overflow-hidden font-sans selection:bg-[#FE7743] selection:text-black">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]" />
      <div className="absolute top-[20%] right-[20%] w-[600px] h-[600px] bg-[#FE7743]/5 rounded-full blur-[120px]" />

      <div className="relative z-10 text-center max-w-lg px-6">
        <div className="mx-auto w-16 h-16 bg-[#FE7743]/10 rounded-full flex items-center justify-center mb-6 border border-[#FE7743]/20">
          <Construction className="text-[#FE7743] w-8 h-8" />
        </div>

        <h1 className="text-4xl font-bold text-white mb-4 tracking-tight">
          Access Request <br />
          <span className="text-[#FE7743]">Coming Soon.</span>
        </h1>

        <p className="text-gray-400 mb-8 leading-relaxed">
          Public registration is currently closed as we scale our
          infrastructure. Please contact{" "}
          <span className="text-white font-mono">support@cleardrive.lk</span>{" "}
          for manual onboarding.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/">
            <Button
              variant="outline"
              className="border-white/10 hover:bg-white/5 text-white gap-2 w-full sm:w-auto h-12"
            >
              <ArrowLeft className="w-4 h-4" /> Return Home
            </Button>
          </Link>
          <Link href="/login">
            <Button className="bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold w-full sm:w-auto h-12">
              Login to Terminal
            </Button>
          </Link>
        </div>

        <div className="mt-12 pt-8 border-t border-white/5 text-xs text-gray-600 font-mono">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Terminal className="w-4 h-4 text-[#FE7743]" />
            ClearDrive<span className="text-[#FE7743]">.lk</span>
          </div>
          SYSTEM UPGRADE IN PROGRESS
        </div>
      </div>
    </div>
  );
}
