"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ClipboardList,
  Package,
  RefreshCcw,
  Ship,
  UploadCloud,
  Radar,
  CheckCircle2,
  Clock,
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
import {
  EXPORTER_TERMS,
  type ExporterOrderFilter,
} from "@/lib/exporter-phrases";

export default function ExporterDashboardPage() {
  const { orders, loading, error, reload, stats } = useAssignedOrders();
  const [filter, setFilter] = useState<ExporterOrderFilter>("all");

  const filteredOrders = useMemo(() => {
    if (filter === "action_required") {
      return orders.filter((order) =>
        ["ASSIGNED_TO_EXPORTER", "AWAITING_SHIPMENT_CONFIRMATION"].includes(
          order.status,
        ),
      );
    }
    if (filter === "in_transit") {
      return orders.filter((order) =>
        [
          "SHIPPED",
          "IN_TRANSIT",
          "ARRIVED_AT_PORT",
          "CUSTOMS_CLEARANCE",
        ].includes(order.status),
      );
    }
    if (filter === "delivered") {
      return orders.filter((order) => order.status === "DELIVERED");
    }
    return orders;
  }, [filter, orders]);

  const filterMeta = [
    { key: "all" as const, label: "All Queue", count: orders.length },
    {
      key: "action_required" as const,
      label: EXPORTER_TERMS.actionRequired,
      count: orders.filter((order) =>
        ["ASSIGNED_TO_EXPORTER", "AWAITING_SHIPMENT_CONFIRMATION"].includes(
          order.status,
        ),
      ).length,
    },
    {
      key: "in_transit" as const,
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
    {
      key: "delivered" as const,
      label: "Delivered",
      count: orders.filter((order) => order.status === "DELIVERED").length,
    },
  ];

  return (
    <ExporterPageShell
      eyebrow={EXPORTER_TERMS.opsBadge}
      title="Assigned"
      accent="Orders."
      description="Review assigned orders, complete shipment tasks, and keep every vehicle export moving on time."
      icon={ClipboardList}
      actions={
        <Button
          variant="outline"
          onClick={() => void reload()}
          className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
        >
          <RefreshCcw className="mr-2 h-4 w-4" />
          Refresh Orders
        </Button>
      }
    >
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {[
          {
            label: "Total Assigned",
            value: String(stats.total),
            icon: ClipboardList,
            sub: "Current queue",
          },
          {
            label: "Awaiting Details",
            value: String(stats.awaitingDetails),
            icon: Clock,
            sub: "Shipping form",
          },
          {
            label: "Awaiting Approval",
            value: String(stats.awaitingApproval),
            icon: Ship,
            sub: "Admin review",
          },
          {
            label: "In Transit",
            value: String(stats.inTransit),
            icon: Radar,
            sub: "Live voyages",
          },
          {
            label: "Delivered",
            value: String(stats.delivered),
            icon: CheckCircle2,
            sub: "Completed",
          },
        ].map((stat) => (
          <ExporterPanel key={stat.label} className="p-4">
            <div className="flex items-start gap-3">
              <div className="rounded-xl border border-[#62929e]/25 bg-[#62929e]/10 p-2 text-[#62929e] dark:border-[#88d6e4]/30 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]">
                <stat.icon className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xl font-semibold text-[#1f2937] dark:text-[#edf2f7]">
                  {stat.value}
                </p>
                <p className="text-[11px] uppercase tracking-[0.16em] text-[#546a7b] dark:text-[#bdcad4]">
                  {stat.label}
                </p>
                <p className="mt-1 text-[11px] text-[#546a7b] dark:text-[#bdcad4]">
                  {stat.sub}
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
          {filterMeta.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setFilter(item.key)}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] transition ${
                filter === item.key
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
          Loading assigned orders...
        </ExporterPanel>
      ) : filteredOrders.length === 0 ? (
        <ExporterEmptyState
          icon={Package}
          title="No matching orders"
          description="Try another filter or refresh. Assigned shipments will appear as soon as operations dispatches them."
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {filteredOrders.map((order) => (
            <ExporterPanel key={order.id} className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-[#546a7b] dark:text-[#bdcad4]">
                    Order ID
                  </p>
                  <p className="mt-2 break-all font-mono text-sm text-[#1f2937] dark:text-[#edf2f7]">
                    {order.id}
                  </p>
                </div>
                <Badge className={getOrderStatusBadgeClass(order.status)}>
                  {order.status.replace(/_/g, " ")}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 text-sm text-[#546a7b] dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65 dark:text-[#bdcad4]">
                <span>{new Date(order.created_at).toLocaleDateString()}</span>
                <span>
                  {order.total_cost_lkr != null
                    ? `LKR ${order.total_cost_lkr.toLocaleString()}`
                    : "Value pending"}
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button
                  asChild
                  className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90"
                >
                  <Link href={`/exporter/shipping?orderId=${order.id}`}>
                    Shipping Details
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                >
                  <Link href={`/exporter/documents?orderId=${order.id}`}>
                    Documents
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                >
                  <Link href={`/exporter/tracking?orderId=${order.id}`}>
                    Tracking
                  </Link>
                </Button>
              </div>
            </ExporterPanel>
          ))}
        </div>
      )}

      <ExporterPanel>
        <h2 className="text-lg font-semibold text-[#1f2937] dark:text-[#edf2f7]">
          Workflow Guide
        </h2>
        <p className="mt-1 text-sm text-[#546a7b] dark:text-[#bdcad4]">
          Complete these steps for each shipment to keep operations smooth.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {[
            {
              title: "Shipping Details",
              desc: "Submit vessel, route, and container data.",
              icon: Ship,
            },
            {
              title: "Documents",
              desc: "Upload required files for review.",
              icon: UploadCloud,
            },
            {
              title: "Tracking",
              desc: "Monitor timeline and status transitions.",
              icon: Radar,
            },
          ].map((step) => (
            <div
              key={step.title}
              className="rounded-2xl border border-[#546a7b]/35 bg-[#c6c5b9]/15 p-4 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65"
            >
              <div className="mb-2 inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[#62929e]/25 bg-[#62929e]/10 text-[#62929e] dark:border-[#88d6e4]/30 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]">
                <step.icon className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-semibold text-[#1f2937] dark:text-[#edf2f7]">
                {step.title}
              </h3>
              <p className="mt-1 text-xs text-[#546a7b] dark:text-[#bdcad4]">
                {step.desc}
              </p>
            </div>
          ))}
        </div>
      </ExporterPanel>
    </ExporterPageShell>
  );
}
