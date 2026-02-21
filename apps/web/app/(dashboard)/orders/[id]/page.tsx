"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Clock3, Download, FileText, Package, Route } from "lucide-react";

import AuthGuard from "@/components/auth/AuthGuard";
import { JourneyTimeline } from "@/components/orders/JourneyTimeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useOrder } from "@/lib/hooks/useOrder";

function OrderTrackingContent() {
  const params = useParams<{ id: string }>();
  const routeId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { data: order, isLoading, error } = useOrder(routeId ?? "");

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#050505] px-6 py-16 text-white">
        <div className="mx-auto max-w-6xl animate-pulse rounded-xl border border-white/10 bg-[#0D0D0D] p-8">
          Loading vehicle journey...
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-[#050505] px-6 py-16 text-white">
        <div className="mx-auto max-w-4xl rounded-xl border border-white/10 bg-[#0D0D0D] p-8 text-center">
          <p className="mb-2 text-lg">Order not found</p>
          {error ? <p className="mb-4 text-sm text-red-400">{error}</p> : null}
          <Button asChild className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90">
            <Link href="/dashboard/orders">Back to Orders</Link>
          </Button>
        </div>
      </div>
    );
  }

  const vehicle = order.vehicle;
  const documents = Array.isArray(order.documents) ? order.documents : [];

  return (
    <div className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <Badge className="bg-[#FE7743]/15 text-[#FE7743]">Order Tracking</Badge>
            <span className="font-mono text-sm text-zinc-400">#{order.id}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Vehicle Journey Timeline</h1>
          <p className="text-zinc-400">
            End-to-end transparency for your import process, from auction to delivery.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-white/10 bg-[#0D0D0D]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Route className="h-5 w-5 text-blue-400" />
                Journey Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <JourneyTimeline currentStep={order.currentStep || 1} />
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card className="border-white/10 bg-[#0D0D0D]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Package className="h-5 w-5 text-[#FE7743]" />
                  Vehicle Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="relative h-52 overflow-hidden rounded-lg border border-white/10">
                  <Image
                    src={
                      vehicle?.imageUrl ||
                      "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80"
                    }
                    alt={`${vehicle?.year || ""} ${vehicle?.make || ""} ${vehicle?.model || ""}`}
                    fill
                    className="object-cover"
                    sizes="(max-width: 1024px) 100vw, 520px"
                  />
                </div>

                <div className="grid gap-2 text-sm">
                  <p className="text-lg font-semibold">
                    {vehicle?.year || "N/A"} {vehicle?.make || "Unknown"}{" "}
                    {vehicle?.model || "Vehicle"}
                  </p>
                  <p className="text-zinc-400">
                    Lot Number: {vehicle?.lotNumber || "Pending"}
                  </p>
                  <p className="text-zinc-400">Color: {vehicle?.color || "Pending"}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-white/10 bg-[#0D0D0D]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Clock3 className="h-5 w-5 text-blue-400" />
                  Live ETA Countdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border border-blue-400/20 bg-blue-500/10 p-4 text-center">
                  <p className="font-mono text-2xl font-bold text-blue-200">
                    {order.etaCountdown || "N/A"}
                  </p>
                  <p className="mt-1 text-xs uppercase tracking-widest text-blue-300">
                    Estimated time to Colombo arrival
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-white/10 bg-[#0D0D0D]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <FileText className="h-5 w-5 text-emerald-400" />
                  Download Documents
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {documents.map((document) => {
                  const isDownloadReady = Boolean(document.downloadUrl);

                  return (
                    <div
                      key={document.id || document.key || document.name}
                      className="flex items-center justify-between rounded-md border border-white/10 bg-black/30 px-3 py-2"
                    >
                      <p className="text-sm text-zinc-200">{document.name}</p>
                      <Button
                        asChild={isDownloadReady}
                        variant="outline"
                        size="sm"
                        disabled={!isDownloadReady}
                        className="border-white/20 bg-transparent text-white hover:bg-white/10"
                      >
                        {isDownloadReady ? (
                          <a
                            href={document.downloadUrl || undefined}
                            download
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Download className="mr-1 h-4 w-4" />
                            Download
                          </a>
                        ) : (
                          <span>Pending</span>
                        )}
                      </Button>
                    </div>
                  );
                })}
                {documents.length === 0 ? (
                  <p className="text-sm text-zinc-400">No documents available yet.</p>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OrderTrackingPage() {
  return (
    <AuthGuard>
      <OrderTrackingContent />
    </AuthGuard>
  );
}
