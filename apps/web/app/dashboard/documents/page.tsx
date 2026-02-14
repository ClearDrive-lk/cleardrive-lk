"use client";

import { FileText, Download, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function DocumentsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <FileText className="w-8 h-8 text-[#FE7743]" />
            Documents
          </h1>
          <p className="text-gray-400 mt-2">
            Manage your invoices, BLs, and customs clearance paperwork.
          </p>
        </div>
        <Badge
          variant="outline"
          className="border-[#FE7743]/20 text-[#FE7743] bg-[#FE7743]/5"
        >
          BETA ACCESS
        </Badge>
      </div>

      {/* Placeholder Content State */}
      <div className="rounded-xl border border-white/10 bg-white/5 border-dashed p-12 text-center relative overflow-hidden group">
        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.02)_50%,transparent_75%,transparent_100%)] bg-[length:250%_250%,100%_100%] bg-[position:-100%_0,0_0] bg-no-repeat transition-[background-position_0s_ease] duration-[1500ms] group-hover:bg-[position:200%_0,0_0]" />

        <div className="relative z-10 flex flex-col items-center max-w-md mx-auto">
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-6">
            <Clock className="w-8 h-8 text-gray-500" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">
            No Documents Available
          </h2>
          <p className="text-gray-400 mb-6">
            Your digital document locker is being provisioned. Once your first
            order is placed, all related paperwork will appear here
            automatically.
          </p>
          <Button className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold">
            View Recent Orders
          </Button>
        </div>
      </div>

      {/* Dummy List for Visual */}
      <div className="mt-12 opacity-50 pointer-events-none blur-[1px] select-none">
        <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">
          Example View
        </h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="flex items-center justify-between p-4 rounded-lg bg-black/20 border border-white/5"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded bg-blue-900/20 flex items-center justify-center text-blue-500">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-white font-medium">
                    Commercial_Invoice_{1000 + i}.pdf
                  </div>
                  <div className="text-xs text-gray-500">
                    2.4 MB • Uploaded 2 days ago
                  </div>
                </div>
              </div>
              <Button variant="ghost" size="sm" className="text-gray-400">
                <Download className="w-4 h-4" />
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
