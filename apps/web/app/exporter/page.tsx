"use client";

import Link from "next/link";
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

export default function ExporterDashboardPage() {
  const { orders, loading, error, reload, stats } = useAssignedOrders();

  return (
    <section className="relative pt-16 pb-20 overflow-hidden flex-1">
      <div className="relative z-10 cd-container space-y-12">
        <div>
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
            </span>
            EXPORTER TERMINAL :: ASSIGNED ORDERS
          </div>

          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-[#393d3f] leading-[0.95]">
                ASSIGNED{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
                  ORDERS.
                </span>
              </h1>
              <p className="mt-4 text-lg text-[#546a7b] max-w-2xl">
                Monitor vehicle export tasks, submit shipping details, and keep
                every shipment moving on schedule.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => void reload()}
              className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
            >
              <RefreshCcw className="w-4 h-4 mr-2" />
              Refresh Orders
            </Button>
          </div>
        </div>

        <div className="border-b border-[#546a7b]/65 bg-[#fdfdff]">
          <div className="grid grid-cols-2 md:grid-cols-5 divide-x divide-white/10">
            {[
              {
                label: "Total Assigned",
                value: String(stats.total),
                icon: ClipboardList,
                sub: "Exporter Queue",
              },
              {
                label: "Awaiting Details",
                value: String(stats.awaitingDetails),
                icon: Clock,
                sub: "Shipping Form",
              },
              {
                label: "Awaiting Approval",
                value: String(stats.awaitingApproval),
                icon: Ship,
                sub: "Admin Review",
              },
              {
                label: "In Transit",
                value: String(stats.inTransit),
                icon: Radar,
                sub: "Live Voyages",
              },
              {
                label: "Delivered",
                value: String(stats.delivered),
                icon: CheckCircle2,
                sub: "Completed",
              },
            ].map((stat, index) => (
              <div
                key={stat.label}
                className={`p-6 flex items-start gap-3 group hover:bg-[#c6c5b9]/20 transition-colors ${
                  index === 0 ? "col-span-2 md:col-span-1" : ""
                }`}
              >
                <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                  <stat.icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xl font-bold text-[#393d3f] tracking-tight">
                    {stat.value}
                  </div>
                  <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                    {stat.label}
                  </div>
                  <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                    {stat.sub}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
            {error}
          </div>
        )}

        {loading ? (
          <div className="rounded-[28px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-12 text-center text-[#546a7b]">
            Loading assigned orders...
          </div>
        ) : orders.length === 0 ? (
          <div className="rounded-[28px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-12 text-center text-[#546a7b]">
            <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-full bg-[#c6c5b9]/20">
              <Package className="h-6 w-6 text-[#62929e]" />
            </div>
            <h2 className="text-2xl font-semibold text-[#393d3f] mb-2">
              No assigned orders yet
            </h2>
            <p className="text-sm text-[#546a7b] max-w-xl mx-auto">
              Assigned orders will appear here as soon as the admin team assigns
              shipments to your exporter account.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {orders.map((order) => (
              <div
                key={order.id}
                className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-[#546a7b]">
                      Order ID
                    </p>
                    <p className="mt-2 font-mono text-sm text-[#393d3f] break-all">
                      {order.id}
                    </p>
                  </div>
                  <Badge
                    className={
                      statusTone[order.status] ??
                      "border-[#546a7b]/65 bg-[#c6c5b9]/20 text-[#393d3f]"
                    }
                  >
                    {order.status.replace(/_/g, " ")}
                  </Badge>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-[#546a7b]">
                  <span>{new Date(order.created_at).toLocaleDateString()}</span>
                  <span>
                    {order.total_cost_lkr != null
                      ? `LKR ${order.total_cost_lkr.toLocaleString()}`
                      : "Value pending"}
                  </span>
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  <Button
                    asChild
                    className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-semibold"
                  >
                    <Link href={`/exporter/shipping?orderId=${order.id}`}>
                      Shipping Details
                    </Link>
                  </Button>
                  <Button
                    asChild
                    variant="outline"
                    className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                  >
                    <Link href={`/exporter/documents?orderId=${order.id}`}>
                      Upload Docs
                    </Link>
                  </Button>
                  <Button
                    asChild
                    variant="outline"
                    className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                  >
                    <Link href={`/exporter/tracking?orderId=${order.id}`}>
                      Track Status
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#fdfdff] p-6">
          <h2 className="text-lg font-semibold text-[#393d3f] mb-2">
            Exporter Workflow
          </h2>
          <p className="text-sm text-[#546a7b] mb-4">
            Follow the workflow for every assigned shipment.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            {[
              {
                title: "Submit Shipping Details",
                desc: "Capture vessel, port, and container details.",
                icon: Ship,
              },
              {
                title: "Upload Documents",
                desc: "Provide required PDFs for admin approval.",
                icon: UploadCloud,
              },
              {
                title: "Monitor Timeline",
                desc: "Track order status updates in real-time.",
                icon: Radar,
              },
            ].map((step) => (
              <div
                key={step.title}
                className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4"
              >
                <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-full bg-[#62929e]/10 text-[#62929e]">
                  <step.icon className="h-4 w-4" />
                </div>
                <h3 className="text-[#393d3f] font-semibold">{step.title}</h3>
                <p className="mt-1 text-xs text-[#546a7b]">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
