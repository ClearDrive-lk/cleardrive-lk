"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CheckCircle2, Copy } from "lucide-react";

import AuthGuard from "@/components/auth/AuthGuard";
import CustomerDashboardNav from "@/components/layout/CustomerDashboardNav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import apiClient from "@/lib/api-client";
import { getOrderStatusBadgeClass } from "@/lib/order-status-badge";

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
      <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        <CustomerDashboardNav />

        <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
        <div className="absolute top-[15%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/5 rounded-[100%] blur-[120px] pointer-events-none" />

        <main className="relative z-10 flex-1 py-16">
          <div className="cd-container-tight">
            <Card className="border-[#546a7b]/65 bg-[#fdfdff]">
              <CardHeader className="space-y-2 text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 border border-emerald-500/30">
                  <CheckCircle2 className="h-7 w-7 text-emerald-700 dark:text-emerald-300" />
                </div>
                <CardTitle className="text-2xl text-[#393d3f]">
                  Order Created
                </CardTitle>
                <p className="text-sm text-[#546a7b]">
                  Your order is locked in. Next, confirm payment to proceed.
                </p>
              </CardHeader>
              <CardContent className="space-y-5">
                {loading ? (
                  <div className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-sm text-[#546a7b]">
                    Loading order details...
                  </div>
                ) : error ? (
                  <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-200">
                    {error}
                  </div>
                ) : order ? (
                  <div className="space-y-3">
                    <div className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-[#546a7b]">
                            Order ID
                          </p>
                          <p className="mt-1 font-mono text-sm text-[#393d3f]">
                            {order.id}
                          </p>
                          <button
                            type="button"
                            onClick={handleCopyOrderId}
                            className="mt-2 inline-flex items-center gap-2 text-xs text-[#546a7b] hover:text-[#393d3f]"
                          >
                            <Copy className="h-3 w-3" />
                            {copied ? "Copied" : "Copy ID"}
                          </button>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge
                            className={getOrderStatusBadgeClass(order.status)}
                          >
                            {order.status.replace(/_/g, " ")}
                          </Badge>
                          <Badge
                            variant="outline"
                            className="border-[#546a7b]/65 text-[#546a7b]"
                          >
                            Payment {order.payment_status.replace(/_/g, " ")}
                          </Badge>
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-[#546a7b]">
                        <span>
                          Created {new Date(order.created_at).toLocaleString()}
                        </span>
                        <span>Total: {formatLkr(order.total_cost_lkr)}</span>
                      </div>
                      {order.vehicle_id && (
                        <div className="mt-3 text-xs text-[#546a7b]">
                          Vehicle ID: {order.vehicle_id}
                        </div>
                      )}
                    </div>

                    <div className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-xs text-[#546a7b]">
                      Shipping address is stored securely and encrypted.
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-sm text-[#546a7b]">
                    Order details unavailable.
                  </div>
                )}

                <div className="flex flex-wrap gap-3">
                  <Button
                    asChild
                    className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
                  >
                    <Link href={`/payment?orderId=${id}`}>
                      Proceed to Payment
                    </Link>
                  </Button>
                  {order?.vehicle_id && (
                    <Button
                      asChild
                      variant="outline"
                      className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                    >
                      <Link href={`/dashboard/vehicles/${order.vehicle_id}`}>
                        View Vehicle
                      </Link>
                    </Button>
                  )}
                  <Button
                    asChild
                    variant="outline"
                    className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
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
