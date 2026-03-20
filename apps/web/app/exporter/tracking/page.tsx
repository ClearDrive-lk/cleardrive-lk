"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Radar, RefreshCcw, PackageCheck, ArrowRight, Ship, UploadCloud } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { OrderTimeline } from "@/components/ui/OrderTimeline";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";
import { getOrderStatusBadgeClass } from "@/lib/order-status-badge";
import {
  ExporterEmptyState,
  ExporterPageShell,
  ExporterPanel,
} from "@/components/exporter/ExporterPageShell";
import { EXPORTER_TERMS } from "@/lib/exporter-phrases";

export default function ExporterTrackingPage() {
  const searchParams = useSearchParams();
  const orderParam = searchParams.get("orderId");
  const { orders, loading, error, reload } = useAssignedOrders();
  const [manualOrderId, setManualOrderId] = useState<string | null>(null);
  const [scope, setScope] = useState<"all" | "attention" | "transit">("all");

  const scopedOrders =
    scope === "attention"
      ? orders.filter((order) =>
          ["ASSIGNED_TO_EXPORTER", "AWAITING_SHIPMENT_CONFIRMATION"].includes(
            order.status,
          ),
        )
      : scope === "transit"
        ? orders.filter((order) =>
            [
              "SHIPPED",
              "IN_TRANSIT",
              "ARRIVED_AT_PORT",
              "CUSTOMS_CLEARANCE",
            ].includes(order.status),
          )
        : orders;

  const selectedOrderId =
    manualOrderId ?? orderParam ?? scopedOrders[0]?.id ?? orders[0]?.id ?? "";
  const selectedOrder =
    scopedOrders.find((order) => order.id === selectedOrderId) ??
    orders.find((order) => order.id === selectedOrderId) ??
    null;

  return (
    <ExporterPageShell
      eyebrow={EXPORTER_TERMS.opsBadge}
      title="Order"
      accent="Tracking."
      description="Monitor timeline events for each order, then jump directly to shipping updates and document uploads."
      icon={Radar}
      actions={
        <Button
          variant="outline"
          onClick={() => void reload()}
          className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
        >
          <RefreshCcw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      }
    >
      {error ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-200">
          {error}
        </div>
      ) : null}

      {loading ? (
        <ExporterPanel className="p-12 text-center text-[#546a7b] dark:text-[#bdcad4]">
          Loading shipment timelines...
        </ExporterPanel>
      ) : orders.length === 0 ? (
        <ExporterEmptyState
          icon={Radar}
          title="No assigned orders available"
          description="Once orders are assigned, you can monitor their timeline updates here."
        />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[340px_minmax(0,1fr)]">
          <ExporterPanel className="space-y-3 p-4 md:p-5">
            <div>
              <h2 className="text-base font-semibold text-[#1f2937] dark:text-[#edf2f7]">
                Shipment Queue
              </h2>
              <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
                Select an order to inspect its timeline.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {[
                { key: "all" as const, label: "All", count: orders.length },
                {
                  key: "attention" as const,
                  label: "Attention",
                  count: orders.filter((order) =>
                    ["ASSIGNED_TO_EXPORTER", "AWAITING_SHIPMENT_CONFIRMATION"].includes(
                      order.status,
                    ),
                  ).length,
                },
                {
                  key: "transit" as const,
                  label: "Transit",
                  count: orders.filter((order) =>
                    [
                      "SHIPPED",
                      "IN_TRANSIT",
                      "ARRIVED_AT_PORT",
                      "CUSTOMS_CLEARANCE",
                    ].includes(order.status),
                  ).length,
                },
              ].map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setScope(item.key)}
                  className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] ${
                    scope === item.key
                      ? "border-[#62929e]/40 bg-[#62929e]/12 text-[#1f2937] dark:border-[#88d6e4]/40 dark:bg-[#88d6e4]/14 dark:text-[#edf2f7]"
                      : "border-[#546a7b]/35 bg-[#c6c5b9]/15 text-[#546a7b] dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65 dark:text-[#bdcad4]"
                  }`}
                >
                  <span>{item.label}</span>
                  <span>{item.count}</span>
                </button>
              ))}
            </div>

            <div className="space-y-2">
              {scopedOrders.map((order) => {
                const selected = order.id === selectedOrderId;
                return (
                  <button
                    key={order.id}
                    type="button"
                    onClick={() => setManualOrderId(order.id)}
                    className={`w-full rounded-2xl border p-3 text-left transition ${
                      selected
                        ? "border-[#62929e]/35 bg-[#62929e]/10 dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/12"
                        : "border-[#546a7b]/35 bg-[#c6c5b9]/15 hover:border-[#62929e]/35 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65 dark:hover:border-[#88d6e4]/35"
                    }`}
                  >
                    <div className="mb-2 flex items-start justify-between gap-3">
                      <p className="break-all font-mono text-xs text-[#1f2937] dark:text-[#edf2f7]">
                        {order.id}
                      </p>
                      <Badge className={getOrderStatusBadgeClass(order.status)}>
                        {order.status.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <div className="text-xs text-[#546a7b] dark:text-[#bdcad4]">
                      {new Date(order.created_at).toLocaleDateString()}
                    </div>
                  </button>
                );
              })}
            </div>
          </ExporterPanel>

          <div className="space-y-4">
            {selectedOrder ? (
              <>
                <ExporterPanel className="space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.18em] text-[#546a7b] dark:text-[#bdcad4]">
                        Selected Order
                      </p>
                      <p className="mt-1 break-all font-mono text-sm text-[#1f2937] dark:text-[#edf2f7]">
                        {selectedOrder.id}
                      </p>
                    </div>
                    <Badge className={getOrderStatusBadgeClass(selectedOrder.status)}>
                      {selectedOrder.status.replace(/_/g, " ")}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      asChild
                      className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90"
                    >
                      <Link href={`/exporter/shipping?orderId=${selectedOrder.id}`}>
                        <Ship className="mr-2 h-4 w-4" />
                        Shipping Details
                      </Link>
                    </Button>
                    <Button
                      asChild
                      variant="outline"
                      className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                    >
                      <Link href={`/exporter/documents?orderId=${selectedOrder.id}`}>
                        <UploadCloud className="mr-2 h-4 w-4" />
                        Documents
                      </Link>
                    </Button>
                    <Button
                      asChild
                      variant="outline"
                      className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                    >
                      <Link href={`/exporter/shipping?orderId=${selectedOrder.id}`}>
                        Edit Details
                        <ArrowRight className="ml-2 h-3.5 w-3.5" />
                      </Link>
                    </Button>
                  </div>

                  <div className="grid gap-2 text-[11px] text-[#546a7b] dark:text-[#bdcad4] md:grid-cols-3">
                    <div className="rounded-xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65">
                      {EXPORTER_TERMS.transitMilestone}
                    </div>
                    <div className="rounded-xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65">
                      {EXPORTER_TERMS.customsReady}
                    </div>
                    <div className="rounded-xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65">
                      Final Delivery ETA
                    </div>
                  </div>
                </ExporterPanel>

                <div className="theme-override">
                  <OrderTimeline orderId={selectedOrder.id} />
                </div>
              </>
            ) : (
              <ExporterEmptyState
                icon={PackageCheck}
                title="No order selected"
                description="Select an order from the queue to view timeline events."
              />
            )}
          </div>
        </div>
      )}
    </ExporterPageShell>
  );
}
