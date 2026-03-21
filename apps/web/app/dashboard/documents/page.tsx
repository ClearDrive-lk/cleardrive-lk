"use client";

import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { FileText } from "lucide-react";
import Link from "next/link";
import AuthGuard from "@/components/auth/AuthGuard";
import CustomerDashboardNav from "@/components/layout/CustomerDashboardNav";
import { Badge } from "@/components/ui/badge";
import apiClient from "@/lib/api-client";
import { ShippingDocumentUpload } from "@/components/shipping/ShippingDocumentUpload";

interface OrderItem {
  id: string;
  status: string;
}

interface OrdersResponse {
  orders: OrderItem[];
}

export default function DocumentsPage() {
  const [orderId, setOrderId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allUploaded, setAllUploaded] = useState(false);

  useEffect(() => {
    const fetchActiveOrder = async () => {
      setLoading(true);
      setError(null);
      try {
        // The API returns an array for /orders. Keep backward-compatible fallback.
        const res = await apiClient.get<OrderItem[] | OrdersResponse>(
          "/orders",
        );
        const orders = Array.isArray(res.data)
          ? res.data
          : Array.isArray(res.data.orders)
            ? res.data.orders
            : [];

        const active =
          orders.find((o) => o.status === "ASSIGNED_TO_EXPORTER") ??
          orders.find((o) => !["DELIVERED", "CANCELLED"].includes(o.status));

        setOrderId(active?.id ?? null);
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load orders.",
          );
        } else {
          setError("Failed to load orders.");
        }
      } finally {
        setLoading(false);
      }
    };

    void fetchActiveOrder();
  }, []);

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] dark:bg-[#0f1417] text-[#1f2937] dark:text-[#edf2f7] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        <CustomerDashboardNav />

        <section className="relative flex-1 overflow-hidden">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
          <div className="absolute top-[8%] left-1/2 -translate-x-1/2 w-[1000px] h-[520px] bg-[#62929e]/6 rounded-[100%] blur-[120px] pointer-events-none" />

          <div className="relative z-10 cd-container-tight py-8">
            <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-[#1f2937] dark:text-[#f1f5f9] tracking-tight flex items-center gap-3">
                  <FileText className="w-8 h-8 text-[#62929e]" />
                  Documents
                </h1>
                <p className="text-[#4f6576] dark:text-[#bdcad4] mt-2">
                  Upload your shipping documents for admin approval.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  href="/dashboard"
                  className="text-sm font-semibold text-[#3f7480] dark:text-[#9edcec] hover:underline"
                >
                  Back to Dashboard
                </Link>
                <Badge
                  variant="outline"
                  className="border-[#62929e]/30 text-[#3f7480] dark:text-[#88d6e4] bg-[#62929e]/5"
                >
                  {allUploaded ? "READY FOR REVIEW" : "IN PROGRESS"}
                </Badge>
              </div>
            </div>

            {loading && (
              <div className="rounded-xl border border-[#546a7b]/55 dark:border-[#8ea3b4]/35 bg-[#c6c5b9]/20 dark:bg-[#233038]/50 p-12 text-center">
                <p className="text-[#4f6576] dark:text-[#c3d0da] text-sm">
                  Loading your order...
                </p>
              </div>
            )}

            {!loading && error && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}

            {!loading && !error && !orderId && (
              <div className="rounded-xl border border-[#546a7b]/55 dark:border-[#8ea3b4]/35 bg-[#c6c5b9]/20 dark:bg-[#233038]/50 border-dashed p-12 text-center">
                <div className="flex flex-col items-center max-w-md mx-auto">
                  <div className="w-16 h-16 rounded-full bg-[#c6c5b9]/20 dark:bg-[#2c3a43] flex items-center justify-center mb-6">
                    <FileText className="w-8 h-8 text-[#546a7b] dark:text-[#b8c8d4]" />
                  </div>
                  <h2 className="text-xl font-bold text-[#1f2937] dark:text-[#edf2f7] mb-2">
                    No Active Shipment
                  </h2>
                  <p className="text-[#4f6576] dark:text-[#c3d0da]">
                    Document upload will be available once an exporter has been
                    assigned to your order.
                  </p>
                </div>
              </div>
            )}

            {!loading && !error && orderId && (
              <div className="rounded-xl border border-[#546a7b]/55 dark:border-[#8ea3b4]/35 bg-[#fdfdff] dark:bg-[#111b21] p-6">
                <ShippingDocumentUpload
                  orderId={orderId}
                  onAllUploaded={() => setAllUploaded(true)}
                />
              </div>
            )}
          </div>
        </section>
      </div>
    </AuthGuard>
  );
}
