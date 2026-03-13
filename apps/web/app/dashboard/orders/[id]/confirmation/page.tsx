"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CheckCircle2, Copy, Terminal } from "lucide-react";

import AuthGuard from "@/components/auth/AuthGuard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import apiClient from "@/lib/api-client";

interface OrderDetail {
  id: string;
  status: string;
  payment_status: string;
  total_cost_lkr: number | string | null;
  created_at: string;
  vehicle_id?: string;
  phone?: string;
}

export default function OrderConfirmationPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const loadOrder = async () => {
      if (!id) return;
      setLoading(true);
      setError(null);
      try {
        const { data } = await apiClient.get<OrderDetail>(`/orders/${id}`);
        setOrder(data);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load order details.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    void loadOrder();
  }, [id]);

  const formatLkr = (value: number | string | null | undefined) => {
    if (value === null || value === undefined) return "N/A";
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "N/A";
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      maximumSignificantDigits: 3,
    }).format(numeric);
  };

  const handleCopyOrderId = async () => {
    if (!order?.id || typeof navigator === "undefined") return;
    try {
      await navigator.clipboard.writeText(order.id);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans flex flex-col">
        <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2"
            >
              <div className="w-8 h-8 bg-[#FE7743]/10 border border-[#FE7743]/20 rounded-md flex items-center justify-center">
                <Terminal className="w-4 h-4 text-[#FE7743]" />
              </div>
              ClearDrive<span className="text-[#FE7743]">.lk</span>
            </Link>
            <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
              <Link
                href="/dashboard"
                className="hover:text-white transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/dashboard/orders"
                className="text-white transition-colors"
              >
                Orders
              </Link>
              <Link
                href="/dashboard/vehicles"
                className="hover:text-white transition-colors"
              >
                Vehicles
              </Link>
            </div>
          </div>
        </nav>

        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
        <div className="absolute top-[15%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#FE7743]/5 rounded-[100%] blur-[120px] pointer-events-none" />

        <main className="relative z-10 flex-1 px-6 py-16">
          <div className="max-w-3xl mx-auto">
            <Card className="border-white/10 bg-[#0F0F0F]">
              <CardHeader className="space-y-2 text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 border border-emerald-500/30">
                  <CheckCircle2 className="h-7 w-7 text-emerald-300" />
                </div>
                <CardTitle className="text-2xl text-white">
                  Order Created
                </CardTitle>
                <p className="text-sm text-gray-400">
                  Your order is locked in. Next, confirm payment to proceed.
                </p>
              </CardHeader>
              <CardContent className="space-y-5">
                {loading ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-gray-400">
                    Loading order details...
                  </div>
                ) : error ? (
                  <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
                    {error}
                  </div>
                ) : order ? (
                  <div className="space-y-3">
                    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-gray-500">
                            Order ID
                          </p>
                          <p className="mt-1 font-mono text-sm text-white">
                            {order.id}
                          </p>
                          <button
                            type="button"
                            onClick={handleCopyOrderId}
                            className="mt-2 inline-flex items-center gap-2 text-xs text-gray-400 hover:text-white"
                          >
                            <Copy className="h-3 w-3" />
                            {copied ? "Copied" : "Copy ID"}
                          </button>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge className="border-white/10 bg-white/5 text-white">
                            {order.status.replace(/_/g, " ")}
                          </Badge>
                          <Badge
                            variant="outline"
                            className="border-white/10 text-gray-300"
                          >
                            Payment {order.payment_status.replace(/_/g, " ")}
                          </Badge>
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-400">
                        <span>
                          Created {new Date(order.created_at).toLocaleString()}
                        </span>
                        <span>Total: {formatLkr(order.total_cost_lkr)}</span>
                      </div>
                      {order.vehicle_id && (
                        <div className="mt-3 text-xs text-gray-500">
                          Vehicle ID: {order.vehicle_id}
                        </div>
                      )}
                    </div>

                    <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-gray-400">
                      Shipping address is stored securely and encrypted.
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-gray-400">
                    Order details unavailable.
                  </div>
                )}

                <div className="flex flex-wrap gap-3">
                  <Button
                    asChild
                    className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold"
                  >
                    <Link href={`/payment?orderId=${id}`}>
                      Proceed to Payment
                    </Link>
                  </Button>
                  {order?.vehicle_id && (
                    <Button
                      asChild
                      variant="outline"
                      className="border-white/10 text-white hover:bg-white/5"
                    >
                      <Link href={`/dashboard/vehicles/${order.vehicle_id}`}>
                        View Vehicle
                      </Link>
                    </Button>
                  )}
                  <Button
                    asChild
                    variant="outline"
                    className="border-white/10 text-white hover:bg-white/5"
                  >
                    <Link href={`/dashboard/orders/${id}`}>View Tracking</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
