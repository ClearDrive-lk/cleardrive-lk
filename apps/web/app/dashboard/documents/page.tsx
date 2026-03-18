"use client";

import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
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
        // Fetch the user's orders and find the one assigned to an exporter
        const res = await apiClient.get<OrdersResponse>("/orders");
        const active = res.data.orders.find(
          (o) => o.status === "ASSIGNED_TO_EXPORTER",
        );
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
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#393d3f] tracking-tight flex items-center gap-3">
            <FileText className="w-8 h-8 text-[#62929e]" />
            Documents
          </h1>
          <p className="text-[#546a7b] mt-2">
            Upload your shipping documents for admin approval.
          </p>
        </div>
        <Badge
          variant="outline"
          className="border-[#62929e]/20 text-[#62929e] bg-[#62929e]/5"
        >
          {allUploaded ? "READY FOR REVIEW" : "IN PROGRESS"}
        </Badge>
      </div>

      {/* Loading */}
      {loading && (
        <div className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-12 text-center">
          <p className="text-[#546a7b] text-sm">Loading your order...</p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* No active order */}
      {!loading && !error && !orderId && (
        <div className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 border-dashed p-12 text-center">
          <div className="flex flex-col items-center max-w-md mx-auto">
            <div className="w-16 h-16 rounded-full bg-[#c6c5b9]/20 flex items-center justify-center mb-6">
              <FileText className="w-8 h-8 text-[#546a7b]" />
            </div>
            <h2 className="text-xl font-bold text-[#393d3f] mb-2">
              No Active Shipment
            </h2>
            <p className="text-[#546a7b]">
              Document upload will be available once an exporter has been
              assigned to your order.
            </p>
          </div>
        </div>
      )}

      {/* Upload component */}
      {!loading && !error && orderId && (
        <div className="rounded-xl border border-[#546a7b]/65 bg-[#fdfdff] p-6">
          <ShippingDocumentUpload
            orderId={orderId}
            onAllUploaded={() => setAllUploaded(true)}
          />
        </div>
      )}
    </div>
  );
}
