"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Sparkles } from "lucide-react";

import AuthGuard from "@/components/auth/AuthGuard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function OrderSuccessContent() {
  const searchParams = useSearchParams();
  const orderId =
    searchParams.get("id") ?? searchParams.get("order_id") ?? "order-demo-001";

  return (
    <div className="min-h-screen bg-[#050505] px-4 py-20 text-white">
      <div className="mx-auto max-w-xl">
        <Card className="border-emerald-500/20 bg-[#0D0D0D] text-white">
          <CardHeader className="text-center">
            <div className="relative mx-auto mb-4 h-20 w-20">
              <span className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" />
              <span className="relative flex h-full w-full items-center justify-center rounded-full border border-emerald-400/30 bg-emerald-500/10">
                <CheckCircle2 className="h-10 w-10 text-emerald-400" />
              </span>
            </div>
            <CardTitle className="text-3xl font-bold">
              Order Confirmed
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-6 text-center">
            <p className="text-zinc-300">
              Your order is now in our transparent import pipeline.
            </p>

            <div className="rounded-md border border-white/10 bg-black/30 p-4">
              <p className="text-xs uppercase tracking-widest text-zinc-400">
                Order ID
              </p>
              <p className="font-mono text-lg text-[#FE7743]">{orderId}</p>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
              <Sparkles className="h-4 w-4" />
              Journey tracking is now active
            </div>

            <Button
              asChild
              className="w-full bg-[#FE7743] font-semibold text-black hover:bg-[#FE7743]/90"
            >
              <Link href={`/orders/${orderId}`}>Track My Vehicle Journey</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function OrderSuccessPage() {
  return (
    <AuthGuard>
      <Suspense fallback={<div className="min-h-screen bg-[#050505]" />}>
        <OrderSuccessContent />
      </Suspense>
    </AuthGuard>
  );
}
