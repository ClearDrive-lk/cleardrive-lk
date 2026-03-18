"use client";

import { ChevronLeft, Gauge, Terminal } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";

function SkeletonLine({
  width,
  height = "h-4",
}: {
  width: string;
  height?: string;
}) {
  return (
    <div className={`${height} ${width} rounded bg-[#c6c5b9]/20 animate-pulse`} />
  );
}

export default function VehicleDetailLoading() {
  return (
    <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none z-0" />

      <nav className="border-b border-[#c6c5b9]/50 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link
            href="/"
            className="font-bold text-xl tracking-tighter flex items-center gap-2"
          >
            <Terminal className="w-5 h-5 text-[#62929e]" />
            ClearDrive<span className="text-[#62929e]">.lk</span>
          </Link>
          <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b]">
            <span>Dashboard</span>
            <span className="text-[#393d3f] flex items-center gap-2">
              Vehicles
              <Badge
                variant="outline"
                className="text-[10px] border-[#62929e]/20 text-[#62929e]"
              >
                LIVE
              </Badge>
            </span>
            <span>KYC</span>
          </div>
        </div>
      </nav>

      <main className="flex-1 relative z-10 max-w-7xl mx-auto w-full px-6 py-8">
        <Button
          variant="ghost"
          disabled
          className="mb-6 pl-0 hover:bg-transparent text-[#546a7b]"
        >
          <ChevronLeft className="w-4 h-4 mr-2" /> Back to Catalog
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="space-y-4">
            <div className="aspect-video w-full rounded-lg bg-[#c6c5b9]/20 border border-[#c6c5b9]/50 animate-pulse" />
            <div className="flex gap-4 overflow-x-auto pb-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="w-24 h-16 rounded border border-[#c6c5b9]/50 bg-[#c6c5b9]/20 animate-pulse flex-shrink-0"
                />
              ))}
            </div>
          </div>

          <div className="space-y-8">
            <div className="space-y-3">
              <SkeletonLine width="w-3/4" height="h-10" />
              <SkeletonLine width="w-1/2" height="h-6" />
              <div className="flex items-center gap-4 mt-4">
                <SkeletonLine width="w-32" />
                <SkeletonLine width="w-20" />
              </div>
            </div>

            <Separator className="bg-[#c6c5b9]/30" />

            <Card className="bg-[#c6c5b9]/20 border-[#c6c5b9]/50 overflow-hidden">
              <CardContent className="p-6 space-y-4">
                <div className="flex justify-between items-end">
                  <SkeletonLine width="w-32" />
                  <SkeletonLine width="w-40" height="h-9" />
                </div>
                <div className="flex justify-between items-center">
                  <SkeletonLine width="w-28" />
                  <SkeletonLine width="w-24" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="h-12 rounded bg-[#62929e]/20 animate-pulse" />
                  <div className="h-12 rounded bg-[#c6c5b9]/20 animate-pulse" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#c6c5b9]/20 border-[#c6c5b9]/50">
              <CardContent className="p-6 space-y-4">
                <h3 className="text-lg font-bold text-[#393d3f] flex items-center gap-2">
                  <Gauge className="w-5 h-5 text-[#62929e]" /> Calculators &
                  Actions
                </h3>
                <SkeletonLine width="w-full" height="h-12" />
                <SkeletonLine width="w-full" height="h-12" />
                <SkeletonLine width="w-full" height="h-32" />
              </CardContent>
            </Card>

            <Card className="bg-[#c6c5b9]/20 border-[#c6c5b9]/50">
              <CardContent className="p-6 space-y-3">
                <h3 className="text-lg font-bold text-[#393d3f]">Specifications</h3>
                {Array.from({ length: 8 }).map((_, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between gap-4"
                  >
                    <SkeletonLine width="w-28" />
                    <SkeletonLine width="w-36" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
