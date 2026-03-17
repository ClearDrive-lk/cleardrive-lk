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
    <div className={`${height} ${width} rounded bg-white/5 animate-pulse`} />
  );
}

export default function VehicleDetailLoading() {
  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans flex flex-col">
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none z-0" />

      <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link
            href="/"
            className="font-bold text-xl tracking-tighter flex items-center gap-2"
          >
            <Terminal className="w-5 h-5 text-[#FE7743]" />
            ClearDrive<span className="text-[#FE7743]">.lk</span>
          </Link>
          <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
            <span>Dashboard</span>
            <span className="text-white flex items-center gap-2">
              Vehicles
              <Badge
                variant="outline"
                className="text-[10px] border-[#FE7743]/20 text-[#FE7743]"
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
          className="mb-6 pl-0 hover:bg-transparent text-gray-400"
        >
          <ChevronLeft className="w-4 h-4 mr-2" /> Back to Catalog
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="space-y-4">
            <div className="aspect-video w-full rounded-lg bg-white/5 border border-white/10 animate-pulse" />
            <div className="flex gap-4 overflow-x-auto pb-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="w-24 h-16 rounded border border-white/10 bg-white/5 animate-pulse flex-shrink-0"
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

            <Separator className="bg-white/10" />

            <Card className="bg-white/5 border-white/10 overflow-hidden">
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
                  <div className="h-12 rounded bg-[#FE7743]/20 animate-pulse" />
                  <div className="h-12 rounded bg-white/5 animate-pulse" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10">
              <CardContent className="p-6 space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Gauge className="w-5 h-5 text-[#FE7743]" /> Calculators &
                  Actions
                </h3>
                <SkeletonLine width="w-full" height="h-12" />
                <SkeletonLine width="w-full" height="h-12" />
                <SkeletonLine width="w-full" height="h-32" />
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10">
              <CardContent className="p-6 space-y-3">
                <h3 className="text-lg font-bold text-white">Specifications</h3>
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
