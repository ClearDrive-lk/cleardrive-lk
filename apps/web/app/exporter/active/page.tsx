"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Flame,
  RefreshCcw,
  Ship,
  UploadCloud,
  Radar,
  Clock3,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ExporterEmptyState,
  ExporterPageShell,
  ExporterPanel,
} from "@/components/exporter/ExporterPageShell";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";
import { getOrderStatusBadgeClass } from "@/lib/order-status-badge";
import { EXPORTER_TERMS } from "@/lib/exporter-phrases";

const NEEDS_EXPORTER_ACTION = new Set([
  "ASSIGNED_TO_EXPORTER",
  "AWAITING_SHIPMENT_CONFIRMATION",
]);

export default function ExporterActivePage() {
  const { orders, loading, error, reload } = useAssignedOrders();
  const [scope, setScope] = useState<"all" | "action" | "transit">("all");

  const activeOrders = useMemo(
    () => orders.filter((order) => !["DELIVERED", "CANCELLED"].includes(order.status)),
    [orders],
  );
  const needsAction = useMemo(
    () => activeOrders.filter((order) => NEEDS_EXPORTER_ACTION.has(order.status)),
    [activeOrders],
  );
  const inTransit = useMemo(
    () =>
      activeOrders.filter((order) =>
        ["SHIPPED", "IN_TRANSIT", "ARRIVED_AT_PORT", "CUSTOMS_CLEARANCE"].includes(
          order.status,
        ),
      ),
    [activeOrders],
  );

  const scopedOrders = useMemo(() => {
    if (scope === "action") return needsAction;
    if (scope === "transit") return inTransit;
    return activeOrders;
  }, [activeOrders, inTransit, needsAction, scope]);

  return (
    <ExporterPageShell
      eyebrow={EXPORTER_TERMS.opsBadge}
      title="Active"
      accent="Shipments."
      description="Focus on the currently active shipment pipeline and quickly jump to details, documents, and tracking."
      icon={Flame}
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
      <div className="grid gap-3 md:grid-cols-3">
        {[
          { label: "Active Orders", value: activeOrders.length, icon: Flame },
          {
            label: EXPORTER_TERMS.actionRequired,
            value: needsAction.length,
            icon: Clock3,
          },
          { label: "Transit Flow", value: inTransit.length, icon: Radar },
        ].map((item) => (
          <ExporterPanel key={item.label} className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-xl border border-[#62929e]/25 bg-[#62929e]/10 p-2 text-[#62929e] dark:border-[#88d6e4]/30 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]">
                <item.icon className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xl font-semibold text-[#1f2937] dark:text-[#edf2f7]">
                  {item.value}
                </p>
                <p className="text-xs uppercase tracking-[0.16em] text-[#546a7b] dark:text-[#bdcad4]">
                  {item.label}
                </p>
              </div>
            </div>
          </ExporterPanel>
        ))}
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-200">
          {error}
        </div>
      ) : null}

      <ExporterPanel className="p-4">
        <div className="flex flex-wrap gap-2">
          {[
            { key: "all" as const, label: "All Active", count: activeOrders.length },
            {
              key: "action" as const,
              label: EXPORTER_TERMS.actionRequired,
              count: needsAction.length,
            },
            { key: "transit" as const, label: "In Transit", count: inTransit.length },
          ].map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setScope(item.key)}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] transition ${
                scope === item.key
                  ? "border-[#62929e]/40 bg-[#62929e]/12 text-[#1f2937] dark:border-[#88d6e4]/40 dark:bg-[#88d6e4]/14 dark:text-[#edf2f7]"
                  : "border-[#546a7b]/35 bg-[#c6c5b9]/15 text-[#546a7b] hover:text-[#1f2937] dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65 dark:text-[#bdcad4] dark:hover:text-[#edf2f7]"
              }`}
            >
              <span>{item.label}</span>
              <span className="rounded-full bg-[#fdfdff]/80 px-1.5 py-0.5 text-[10px] dark:bg-[#10191e]/80">
                {item.count}
              </span>
            </button>
          ))}
        </div>
      </ExporterPanel>

      {loading ? (
        <ExporterPanel className="p-12 text-center text-[#546a7b] dark:text-[#bdcad4]">
          Loading active shipments...
        </ExporterPanel>
      ) : scopedOrders.length === 0 ? (
        <ExporterEmptyState
          icon={Flame}
          title="No orders in this lane"
          description="Switch scope or refresh once new shipment tasks are assigned."
        />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {scopedOrders.map((order) => (
            <ExporterPanel key={order.id} className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-[#546a7b] dark:text-[#bdcad4]">
                    Active Order
                  </p>
                  <p className="mt-1 break-all font-mono text-sm text-[#1f2937] dark:text-[#edf2f7]">
                    {order.id}
                  </p>
                </div>
                <Badge className={getOrderStatusBadgeClass(order.status)}>
                  {order.status.replace(/_/g, " ")}
                </Badge>
              </div>

              <div className="rounded-2xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 text-sm text-[#546a7b] dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65 dark:text-[#bdcad4]">
                {new Date(order.created_at).toLocaleDateString()} -{" "}
                {order.total_cost_lkr != null
                  ? `LKR ${order.total_cost_lkr.toLocaleString()}`
                  : "Value pending"}
              </div>

              <div className="flex flex-wrap gap-2">
                <Button
                  asChild
                  className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90"
                >
                  <Link href={`/exporter/shipping?orderId=${order.id}`}>
                    <Ship className="mr-2 h-4 w-4" />
                    Shipping
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                >
                  <Link href={`/exporter/documents?orderId=${order.id}`}>
                    <UploadCloud className="mr-2 h-4 w-4" />
                    Docs
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                >
                  <Link href={`/exporter/tracking?orderId=${order.id}`}>
                    <Radar className="mr-2 h-4 w-4" />
                    Tracking
                  </Link>
                </Button>
              </div>
            </ExporterPanel>
          ))}
        </div>
      )}
    </ExporterPageShell>
  );
}
