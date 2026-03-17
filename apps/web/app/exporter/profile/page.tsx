"use client";

import { useAppSelector } from "@/lib/store/store";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { User, Mail, Shield, Terminal, BarChart3 } from "lucide-react";

export default function ExporterProfilePage() {
  const { user } = useAppSelector((state) => state.auth);
  const { stats } = useAssignedOrders();

  return (
    <section className="relative pt-16 pb-20 px-6 overflow-hidden flex-1">
      <div className="relative z-10 max-w-5xl mx-auto space-y-12">
        <div>
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743] mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
            </span>
            EXPORTER PROFILE :: ACCOUNT OVERVIEW
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-white">
            EXPORTER{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
              PROFILE.
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-400 max-w-2xl">
            Keep your exporter identity and workflow metrics up to date.
          </p>
        </div>

        {user && (
          <div className="border border-white/10 rounded-[24px] bg-white/[0.03] divide-y divide-white/10">
            <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-white/10">
              <div className="p-6 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xl font-bold text-white tracking-tight">
                    {user.name}
                  </div>
                  <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">
                    Full Name
                  </div>
                  <div className="text-[10px] text-gray-600 font-mono mt-1">
                    Exporter Account
                  </div>
                </div>
              </div>

              <div className="p-6 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xl font-bold text-white tracking-tight break-all">
                    {user.email}
                  </div>
                  <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">
                    Email Address
                  </div>
                  <div className="text-[10px] text-gray-600 font-mono mt-1">
                    Verified Contact
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-white/10">
              <div className="p-6 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xl font-bold text-white tracking-tight">
                    {user.role}
                  </div>
                  <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">
                    Access Role
                  </div>
                  <div className="text-[10px] text-gray-600 font-mono mt-1">
                    Export Pipeline
                  </div>
                </div>
              </div>

              <div className="p-6 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-mono text-white opacity-80 tracking-tight break-all">
                    {user.id}
                  </div>
                  <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">
                    Exporter ID
                  </div>
                  <div className="text-[10px] text-gray-600 font-mono mt-1">
                    Internal Reference
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="rounded-[24px] border border-white/10 bg-[#0A0A0A] p-6">
          <div className="flex items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">
                Exporter Metrics
              </h2>
              <p className="text-sm text-gray-500">
                Snapshot of your current workload.
              </p>
            </div>
            <Badge
              variant="outline"
              className="border-[#FE7743]/20 text-[#FE7743]"
            >
              LIVE
            </Badge>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Assigned", value: stats.total },
              { label: "Awaiting Details", value: stats.awaitingDetails },
              { label: "In Transit", value: stats.inTransit },
              { label: "Delivered", value: stats.delivered },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-white/10 bg-white/[0.02] p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-[#FE7743]/10 p-2 text-[#FE7743]">
                    <BarChart3 className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-xl font-semibold text-white">
                      {item.value}
                    </div>
                    <div className="text-xs text-gray-500">{item.label}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 text-xs text-gray-500">
            Metrics update in real-time as shipments progress through the
            workflow.
          </div>
        </div>

        <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-6">
          <h2 className="text-lg font-semibold text-white mb-2">
            Exporter Support
          </h2>
          <p className="text-sm text-gray-400 mb-4">
            Need help with documents or shipping status updates? Reach the
            operations desk.
          </p>
          <Button
            variant="outline"
            className="border-white/10 text-white hover:bg-white/5"
          >
            Contact Ops Desk
          </Button>
        </div>
      </div>
    </section>
  );
}
