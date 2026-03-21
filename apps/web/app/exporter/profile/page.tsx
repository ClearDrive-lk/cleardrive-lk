"use client";

import Link from "next/link";
import { useMemo } from "react";
import {
  User,
  Mail,
  Shield,
  Terminal,
  BarChart3,
  CircleGauge,
  LifeBuoy,
  ArrowRight,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAppSelector } from "@/lib/store/store";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";
import {
  ExporterPageShell,
  ExporterPanel,
} from "@/components/exporter/ExporterPageShell";
import { EXPORTER_TERMS } from "@/lib/exporter-phrases";

export default function ExporterProfilePage() {
  const { user } = useAppSelector((state) => state.auth);
  const { stats } = useAssignedOrders();

  const completionRate = useMemo(() => {
    if (stats.total === 0) return 0;
    return Math.round((stats.delivered / stats.total) * 100);
  }, [stats.delivered, stats.total]);
  const serviceGrade =
    completionRate >= 80 ? "A" : completionRate >= 60 ? "B" : "C";

  const identityCards = [
    { label: "Full Name", value: user?.name ?? "N/A", icon: User },
    { label: "Email", value: user?.email ?? "N/A", icon: Mail, breakAll: true },
    { label: "Role", value: user?.role ?? "N/A", icon: Shield },
    {
      label: "Exporter ID",
      value: user?.id ?? "N/A",
      icon: Terminal,
      mono: true,
      breakAll: true,
    },
  ];

  return (
    <ExporterPageShell
      eyebrow={EXPORTER_TERMS.opsBadge}
      title="Exporter"
      accent="Profile."
      description="Manage identity details, monitor shipment performance, and keep your export workflow aligned."
      icon={User}
      width="narrow"
      actions={
        <div className="flex flex-wrap gap-2">
          <Badge
            variant="outline"
            className="border-[#62929e]/25 bg-[#62929e]/8 text-[#62929e] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]"
          >
            Live Metrics
          </Badge>
          <Badge
            variant="outline"
            className="border-[#546a7b]/35 bg-[#c6c5b9]/15 text-[#546a7b] dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65 dark:text-[#bdcad4]"
          >
            Export Service Grade {serviceGrade}
          </Badge>
        </div>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {identityCards.map((item) => (
          <ExporterPanel key={item.label} className="p-4">
            <div className="flex items-start gap-3">
              <div className="rounded-xl border border-[#62929e]/25 bg-[#62929e]/10 p-2 text-[#62929e] dark:border-[#88d6e4]/30 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]">
                <item.icon className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] uppercase tracking-[0.16em] text-[#546a7b] dark:text-[#bdcad4]">
                  {item.label}
                </p>
                <p
                  className={`mt-1 text-sm font-semibold text-[#1f2937] dark:text-[#edf2f7] ${
                    item.mono ? "font-mono" : ""
                  } ${item.breakAll ? "break-all" : ""}`}
                >
                  {item.value}
                </p>
              </div>
            </div>
          </ExporterPanel>
        ))}
      </div>

      <ExporterPanel>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-[#1f2937] dark:text-[#edf2f7]">
              Exporter Metrics
            </h2>
            <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
              Real-time overview of your shipment pipeline.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[#62929e]/25 bg-[#62929e]/10 px-3 py-1 text-xs text-[#62929e] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]">
            <CircleGauge className="h-3.5 w-3.5" />
            Completion Rate {completionRate}%
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Assigned", value: stats.total },
            { label: "Awaiting Details", value: stats.awaitingDetails },
            { label: "In Transit", value: stats.inTransit },
            { label: "Delivered", value: stats.delivered },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-2xl border border-[#546a7b]/35 bg-[#c6c5b9]/15 p-4 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65"
            >
              <div className="flex items-center gap-2">
                <div className="rounded-lg border border-[#62929e]/25 bg-[#62929e]/10 p-1.5 text-[#62929e] dark:border-[#88d6e4]/30 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]">
                  <BarChart3 className="h-3.5 w-3.5" />
                </div>
                <p className="text-lg font-semibold text-[#1f2937] dark:text-[#edf2f7]">
                  {item.value}
                </p>
              </div>
              <p className="mt-2 text-xs uppercase tracking-[0.14em] text-[#546a7b] dark:text-[#bdcad4]">
                {item.label}
              </p>
            </div>
          ))}
        </div>
      </ExporterPanel>

      <div className="grid gap-4 md:grid-cols-2">
        <ExporterPanel>
          <h3 className="text-base font-semibold text-[#1f2937] dark:text-[#edf2f7]">
            Workflow Shortcuts
          </h3>
          <p className="mt-1 text-sm text-[#546a7b] dark:text-[#bdcad4]">
            Jump into active orders and operational tools.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              asChild
              className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90"
            >
              <Link href="/exporter/active">Open Active Orders</Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
            >
              <Link href="/exporter/tracking">
                View Tracking <ArrowRight className="ml-2 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </ExporterPanel>

        <ExporterPanel>
          <h3 className="text-base font-semibold text-[#1f2937] dark:text-[#edf2f7]">
            Exporter Support
          </h3>
          <p className="mt-1 text-sm text-[#546a7b] dark:text-[#bdcad4]">
            Reach operations for shipment blockers, missing docs, or approval
            delays.
          </p>
          <Button
            asChild
            variant="outline"
            className="mt-4 border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
          >
            <a href="mailto:ops@cleardrive.lk">
              <LifeBuoy className="mr-2 h-4 w-4" />
              Contact Ops Desk
            </a>
          </Button>
        </ExporterPanel>
      </div>
    </ExporterPageShell>
  );
}
