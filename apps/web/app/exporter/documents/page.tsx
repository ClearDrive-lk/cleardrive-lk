"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FileText, RefreshCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShippingDocumentUpload } from "@/components/shipping/ShippingDocumentUpload";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";

export default function ExporterDocumentsPage() {
  const searchParams = useSearchParams();
  const orderParam = searchParams.get("orderId");
  const { orders, loading, error, reload } = useAssignedOrders();
  const [manualOrderId, setManualOrderId] = useState<string | null>(null);
  const [uploadState, setUploadState] = useState<Record<string, boolean>>({});

  const selectedOrderId = manualOrderId ?? orderParam ?? orders[0]?.id ?? "";

  const allUploaded = useMemo(() => {
    if (!selectedOrderId) return false;
    return uploadState[selectedOrderId] ?? false;
  }, [selectedOrderId, uploadState]);

  return (
    <section className="relative pt-16 pb-20 overflow-hidden flex-1">
      <div className="relative z-10 cd-container space-y-8">
        <div>
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
            </span>
            DOCUMENT UPLOAD :: EXPORTER WORKFLOW
          </div>

          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-[#393d3f]">
                SHIPPING{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
                  DOCUMENTS.
                </span>
              </h1>
              <p className="mt-4 text-lg text-[#546a7b] max-w-2xl">
                Upload all required documents to move shipments into admin
                approval.
              </p>
            </div>
            <Badge
              variant="outline"
              className="border-[#62929e]/20 text-[#62929e] bg-[#62929e]/5"
            >
              {allUploaded ? "READY FOR REVIEW" : "IN PROGRESS"}
            </Badge>
          </div>
        </div>

        <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-[#393d3f]">
                Select Assigned Order
              </h2>
              <p className="text-sm text-[#546a7b]">
                Upload documents for the selected shipment.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => void reload()}
              className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
            >
              <RefreshCcw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
              {error}
            </div>
          )}

          <select
            className="h-11 w-full rounded-xl bg-[#fdfdff]/60 border border-[#546a7b]/65 px-3 text-sm text-[#393d3f]"
            value={selectedOrderId}
            onChange={(e) => {
              const next = e.target.value;
              setManualOrderId(next ? next : null);
            }}
            disabled={loading && !orders.length}
          >
            <option value="">Select an order</option>
            {orders.map((order) => (
              <option key={order.id} value={order.id}>
                {order.id} - {order.status.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>

        {!selectedOrderId ? (
          <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-12 text-center text-[#546a7b]">
            <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-full bg-[#c6c5b9]/20">
              <FileText className="h-6 w-6 text-[#62929e]" />
            </div>
            Select an order to begin uploading shipping documents.
          </div>
        ) : (
          <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#fdfdff] p-6">
            <ShippingDocumentUpload
              orderId={selectedOrderId}
              onAllUploaded={() => {
                if (!selectedOrderId) return;
                setUploadState((prev) => ({
                  ...prev,
                  [selectedOrderId]: true,
                }));
              }}
            />
          </div>
        )}
      </div>
    </section>
  );
}
