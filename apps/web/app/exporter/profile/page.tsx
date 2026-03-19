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
    <section className="relative pt-16 pb-20 overflow-hidden flex-1">
      <div className="relative z-10 cd-container-narrow space-y-12">
        <div>
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
            </span>
            EXPORTER PROFILE :: ACCOUNT OVERVIEW
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-[#393d3f]">
            EXPORTER{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
              PROFILE.
            </span>
          </h1>
          <p className="mt-4 text-lg text-[#546a7b] max-w-2xl">
            Keep your exporter identity and workflow metrics up to date.
          </p>
        </div>

        {user && (
          <div className="border border-[#546a7b]/65 rounded-[24px] bg-[#c6c5b9]/20 divide-y divide-white/10">
            <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-white/10">
              <div className="p-6 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xl font-bold text-[#393d3f] tracking-tight">
                    {user.name}
                  </div>
                  <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                    Full Name
                  </div>
                  <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                    Exporter Account
                  </div>
                </div>
              </div>

              <div className="p-6 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xl font-bold text-[#393d3f] tracking-tight break-all">
                    {user.email}
                  </div>
                  <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                    Email Address
                  </div>
                  <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                    Verified Contact
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-white/10">
              <div className="p-6 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xl font-bold text-[#393d3f] tracking-tight">
                    {user.role}
                  </div>
                  <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                    Access Role
                  </div>
                  <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                    Export Pipeline
                  </div>
                </div>
              </div>

              <div className="p-6 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-mono text-[#393d3f] opacity-80 tracking-tight break-all">
                    {user.id}
                  </div>
                  <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                    Exporter ID
                  </div>
                  <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                    Internal Reference
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#fdfdff] p-6">
          <div className="flex items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-lg font-semibold text-[#393d3f]">
                Exporter Metrics
              </h2>
              <p className="text-sm text-[#546a7b]">
                Snapshot of your current workload.
              </p>
            </div>
            <Badge
              variant="outline"
              className="border-[#62929e]/20 text-[#62929e]"
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
                className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-[#62929e]/10 p-2 text-[#62929e]">
                    <BarChart3 className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-xl font-semibold text-[#393d3f]">
                      {item.value}
                    </div>
                    <div className="text-xs text-[#546a7b]">{item.label}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 text-xs text-[#546a7b]">
            Metrics update in real-time as shipments progress through the
            workflow.
          </div>
        </div>

        <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
          <h2 className="text-lg font-semibold text-[#393d3f] mb-2">
            Exporter Support
          </h2>
          <p className="text-sm text-[#546a7b] mb-4">
            Need help with documents or shipping status updates? Reach the
            operations desk.
          </p>
          <Button
            variant="outline"
            className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
          >
            Contact Ops Desk
          </Button>
        </div>
      </div>
    </section>
  );
}
