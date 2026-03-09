"use client";

import { useEffect, useMemo, useState } from "react";

import AuthGuard from "@/components/auth/AuthGuard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { OrderTimeline } from "@/components/ui/OrderTimeline";
import apiClient from "@/lib/api-client";
import { useLogout } from "@/lib/hooks/useLogout";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  Package,
  RefreshCcw,
  Terminal,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";

type OrderListItem = {
  id: string;
  status: string;
  payment_status: string;
  total_cost_lkr: number | null;
  created_at: string;
};

const statusTone: Record<string, string> = {
  CREATED: "border-sky-500/20 bg-sky-500/10 text-sky-200",
  PAYMENT_CONFIRMED: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
  ASSIGNED_TO_EXPORTER:
    "border-fuchsia-500/20 bg-fuchsia-500/10 text-fuchsia-200",
  SHIPPED: "border-indigo-500/20 bg-indigo-500/10 text-indigo-200",
  IN_TRANSIT: "border-cyan-500/20 bg-cyan-500/10 text-cyan-200",
  DELIVERED: "border-emerald-500/20 bg-emerald-500/10 text-emerald-100",
  CANCELLED: "border-red-500/20 bg-red-500/10 text-red-200",
};

export default function OrdersPage() {
  const { logout, isLoading } = useLogout();
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    void loadOrders();
  }, []);

  const loadOrders = async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setPageLoading(true);
      setPageError(null);
    }

    try {
      const { data } = await apiClient.get<OrderListItem[]>("/orders");
      setOrders(data);
      setSelectedOrderId((current) => current ?? data[0]?.id ?? null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load orders.";
      setPageError(message);
    } finally {
      if (!silent) {
        setPageLoading(false);
      }
    }
  };

  const stats = useMemo(() => {
    const total = orders.length;
    const active = orders.filter(
      (order) => !["DELIVERED", "CANCELLED"].includes(order.status),
    ).length;
    const completed = orders.filter(
      (order) => order.status === "DELIVERED",
    ).length;
    const avgValue =
      total === 0
        ? null
        : Math.round(
            orders.reduce(
              (sum, order) => sum + (order.total_cost_lkr ?? 0),
              0,
            ) / total,
          );

    return { total, active, completed, avgValue };
  }, [orders]);

  const selectedOrder =
    orders.find((order) => order.id === selectedOrderId) ?? null;

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
                className="text-white transition-colors flex items-center gap-2"
              >
                Orders{" "}
                <Badge
                  variant="outline"
                  className="text-[10px] border-[#FE7743]/20 text-[#FE7743] h-4 px-1"
                >
                  ACTIVE
                </Badge>
              </Link>
              <Link
                href="/dashboard/vehicles"
                className="hover:text-white transition-colors"
              >
                Vehicles
              </Link>
              <Link
                href="/dashboard/kyc"
                className="hover:text-white transition-colors"
              >
                KYC
              </Link>
              <Link
                href="/dashboard/shipping"
                className="hover:text-white transition-colors"
              >
                Shipping
              </Link>
              <Link
                href="/dashboard/kyc"
                className="hover:text-white transition-colors"
              >
                KYC
              </Link>
              <Link
                href="/dashboard/profile"
                className="hover:text-white transition-colors"
              >
                Profile
              </Link>
            </div>
            <Button
              onClick={logout}
              disabled={isLoading}
              className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold"
            >
              {isLoading ? "Signing Out..." : "Sign Out"}
            </Button>
          </div>
        </nav>

        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#FE7743]/5 rounded-[100%] blur-[120px] pointer-events-none" />

        <section className="relative pt-20 pb-20 px-6 overflow-hidden flex-1">
          <div className="relative z-10 max-w-7xl mx-auto">
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743] mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
              </span>
              ORDER MANAGEMENT :: CLEARANCE TRACKING
            </div>

            <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-white leading-[0.9] mb-6">
              YOUR{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
                ORDERS.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-gray-400 max-w-2xl mb-12">
              Track your vehicle clearance orders with a live status timeline
              and inspect every milestone in one place.
            </p>

            <div className="border-b border-white/10 bg-[#0A0A0A] mb-12">
              <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-white/10">
                {[
                  {
                    label: "Total Orders",
                    value: String(stats.total),
                    icon: Package,
                    sub: "All Time",
                  },
                  {
                    label: "In Progress",
                    value: String(stats.active),
                    icon: Clock,
                    sub: "Active Now",
                  },
                  {
                    label: "Completed",
                    value: String(stats.completed),
                    icon: CheckCircle2,
                    sub: "Delivered",
                  },
                  {
                    label: "Avg. Value",
                    value: stats.avgValue
                      ? `LKR ${stats.avgValue.toLocaleString()}`
                      : "N/A",
                    icon: TrendingUp,
                    sub: "Per Order",
                  },
                ].map((stat, i) => (
                  <div
                    key={i}
                    className="p-8 flex items-start gap-4 group hover:bg-white/5 transition-colors cursor-default"
                  >
                    <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                      <stat.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xl font-bold text-white tracking-tight">
                        {stat.value}
                      </div>
                      <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">
                        {stat.label}
                      </div>
                      <div className="text-[10px] text-gray-600 font-mono mt-1">
                        {stat.sub}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {pageError && (
              <div className="mb-8 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
                {pageError}
              </div>
            )}

            {pageLoading ? (
              <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-10 text-center text-gray-400">
                Loading orders...
              </div>
            ) : orders.length === 0 ? (
              <div className="max-w-2xl mx-auto p-1 rounded-xl bg-gradient-to-b from-white/10 to-white/5 backdrop-blur-xl border border-white/10 shadow-2xl">
                <div className="text-center bg-[#0A0A0A] rounded-lg p-16">
                  <div className="inline-flex p-6 rounded-full bg-[#FE7743]/10 border border-[#FE7743]/20 mb-6">
                    <Package className="w-16 h-16 text-[#FE7743]" />
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-4 tracking-tight">
                    No Orders Yet
                  </h2>
                  <p className="text-lg text-gray-400 mb-8 leading-relaxed">
                    Start your first vehicle import order. Access live auction
                    data from USS Tokyo, JAA, and CAI.
                  </p>
                  <Button
                    asChild
                    className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold gap-2"
                  >
                    <Link href="/dashboard/vehicles">
                      Browse Auctions <ArrowRight className="w-4 h-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid gap-8 lg:grid-cols-[380px_minmax(0,1fr)]">
                <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-white">
                        Order Queue
                      </h2>
                      <p className="text-sm text-gray-500">
                        Select an order to inspect its timeline.
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => void loadOrders()}
                      className="text-gray-400 hover:bg-white/5 hover:text-white"
                    >
                      <RefreshCcw className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="space-y-3">
                    {orders.map((order) => {
                      const selected = order.id === selectedOrderId;
                      return (
                        <button
                          key={order.id}
                          type="button"
                          onClick={() => setSelectedOrderId(order.id)}
                          className={`w-full rounded-2xl border p-4 text-left transition-colors ${
                            selected
                              ? "border-[#FE7743]/40 bg-[#FE7743]/10"
                              : "border-white/10 bg-[#0C0C0C] hover:bg-white/[0.05]"
                          }`}
                        >
                          <div className="mb-3 flex items-start justify-between gap-3">
                            <div>
                              <p className="text-xs uppercase tracking-[0.25em] text-gray-500">
                                Order
                              </p>
                              <p className="mt-1 font-mono text-sm text-white">
                                {order.id}
                              </p>
                            </div>
                            <Badge
                              className={
                                statusTone[order.status] ??
                                "border-white/10 bg-white/5 text-white"
                              }
                            >
                              {order.status.replace(/_/g, " ")}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between text-sm text-gray-400">
                            <span>
                              {new Date(order.created_at).toLocaleDateString()}
                            </span>
                            <span>
                              {order.total_cost_lkr != null
                                ? `LKR ${order.total_cost_lkr.toLocaleString()}`
                                : "Value pending"}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="space-y-4">
                  {selectedOrder ? (
                    <>
                      <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
                        <div className="flex flex-wrap items-center justify-between gap-4">
                          <div>
                            <p className="text-xs uppercase tracking-[0.25em] text-gray-500">
                              Selected Order
                            </p>
                            <p className="mt-2 font-mono text-lg text-white">
                              {selectedOrder.id}
                            </p>
                          </div>
                          <div className="flex flex-wrap items-center gap-3">
                            <Badge
                              className={
                                statusTone[selectedOrder.status] ??
                                "border-white/10 bg-white/5 text-white"
                              }
                            >
                              {selectedOrder.status.replace(/_/g, " ")}
                            </Badge>
                            <Badge
                              variant="outline"
                              className="border-white/10 text-gray-300"
                            >
                              Payment {selectedOrder.payment_status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <OrderTimeline
                        orderId={selectedOrder.id}
                        onTimelineUpdate={() => {
                          void loadOrders({ silent: true });
                        }}
                      />
                    </>
                  ) : null}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </AuthGuard>
  );
}
