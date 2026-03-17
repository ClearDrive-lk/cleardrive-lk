"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Radar, RefreshCcw, PackageCheck, ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { OrderTimeline } from "@/components/ui/OrderTimeline";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";

const statusTone: Record<string, string> = {
  ASSIGNED_TO_EXPORTER:
    "border-fuchsia-500/20 bg-fuchsia-500/10 text-fuchsia-200",
  AWAITING_SHIPMENT_CONFIRMATION:
    "border-orange-500/20 bg-orange-500/10 text-orange-200",
  SHIPPED: "border-indigo-500/20 bg-indigo-500/10 text-indigo-200",
  IN_TRANSIT: "border-cyan-500/20 bg-cyan-500/10 text-cyan-200",
  ARRIVED_AT_PORT: "border-teal-500/20 bg-teal-500/10 text-teal-200",
  CUSTOMS_CLEARANCE: "border-yellow-500/20 bg-yellow-500/10 text-yellow-200",
  DELIVERED: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
  CANCELLED: "border-red-500/20 bg-red-500/10 text-red-200",
};

export default function ExporterTrackingPage() {
  const searchParams = useSearchParams();
  const orderParam = searchParams.get("orderId");
  const { orders, loading, error, reload } = useAssignedOrders();
  const [selectedOrderId, setSelectedOrderId] = useState(orderParam ?? "");

  useEffect(() => {
    if (!selectedOrderId && orders.length > 0) {
      setSelectedOrderId(orders[0].id);
    }
  }, [orders, selectedOrderId]);

  useEffect(() => {
    if (orderParam) {
      setSelectedOrderId(orderParam);
    }
  }, [orderParam]);

  const selectedOrder =
    orders.find((order) => order.id === selectedOrderId) ?? null;

  return (
    <section className="relative pt-16 pb-20 px-6 overflow-hidden flex-1">
      <div className="relative z-10 max-w-7xl mx-auto space-y-10">
        <div>
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743] mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
            </span>
            SHIPMENT STATUS :: LIVE TRACKING
          </div>

          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-white">
                SHIPMENT{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
                  TRACKING.
                </span>
              </h1>
              <p className="mt-4 text-lg text-gray-400 max-w-2xl">
                Follow each order timeline, review status changes, and share
                updates with the logistics team.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => void reload()}
              className="border-white/10 text-white hover:bg-white/5"
            >
              <RefreshCcw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
            {error}
          </div>
        )}

        {loading ? (
          <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-12 text-center text-gray-400">
            Loading shipment timelines...
          </div>
        ) : orders.length === 0 ? (
          <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-12 text-center text-gray-400">
            <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-full bg-white/5">
              <Radar className="h-6 w-6 text-[#FE7743]" />
            </div>
            No assigned orders available for tracking yet.
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-[360px_minmax(0,1fr)]">
            <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">
                    Shipment Queue
                  </h2>
                  <p className="text-sm text-gray-500">
                    Select an order to view its timeline.
                  </p>
                </div>
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
                          <p className="mt-1 font-mono text-sm text-white break-all">
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
                  <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-6">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.25em] text-gray-500">
                          Selected Order
                        </p>
                        <p className="mt-2 font-mono text-lg text-white break-all">
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
                        <Button
                          asChild
                          variant="outline"
                          className="border-white/10 text-white hover:bg-white/5"
                        >
                          <Link
                            href={`/exporter/shipping?orderId=${selectedOrder.id}`}
                          >
                            Update Shipping
                          </Link>
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-[24px] border border-white/10 bg-[#0A0A0A] p-5">
                    <h3 className="text-sm font-semibold text-white">
                      Quick Actions
                    </h3>
                    <p className="mt-1 text-xs text-gray-500">
                      Jump to documents or share the timeline with the team.
                    </p>
                    <div className="mt-4 flex flex-wrap gap-3">
                      <Button
                        asChild
                        className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-semibold"
                      >
                        <Link
                          href={`/exporter/documents?orderId=${selectedOrder.id}`}
                        >
                          Upload Documents
                        </Link>
                      </Button>
                      <Button
                        asChild
                        variant="outline"
                        className="border-white/10 text-white hover:bg-white/5"
                      >
                        <Link
                          href={`/exporter/shipping?orderId=${selectedOrder.id}`}
                        >
                          Shipping Details{" "}
                          <ArrowRight className="ml-1 h-3 w-3" />
                        </Link>
                      </Button>
                    </div>
                  </div>

                  <OrderTimeline orderId={selectedOrder.id} />
                </>
              ) : (
                <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-10 text-center text-gray-400">
                  <PackageCheck className="mx-auto mb-4 h-6 w-6 text-[#FE7743]" />
                  Select an order to view its shipment timeline.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
