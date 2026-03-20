"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FileText, RefreshCcw, UploadCloud } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShippingDocumentUpload } from "@/components/shipping/ShippingDocumentUpload";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";
import {
  ExporterEmptyState,
  ExporterPageShell,
  ExporterPanel,
} from "@/components/exporter/ExporterPageShell";
import { EXPORTER_TERMS } from "@/lib/exporter-phrases";

const selectClass =
  "h-11 w-full rounded-xl border border-[#546a7b]/45 bg-[#fdfdff]/80 px-3 text-sm text-[#1f2937] outline-none transition focus:border-[#62929e]/65 focus:ring-2 focus:ring-[#62929e]/20 dark:border-[#8fa3b1]/35 dark:bg-[#1a272f]/80 dark:text-[#edf2f7] dark:focus:border-[#88d6e4]/60 dark:focus:ring-[#88d6e4]/20";

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
    <ExporterPageShell
      eyebrow={EXPORTER_TERMS.opsBadge}
      title="Shipping"
      accent="Documents."
      description="Upload mandatory shipping documents and keep each order moving toward admin approval."
      icon={UploadCloud}
      actions={
        <Badge
          variant="outline"
          className="border-[#62929e]/25 bg-[#62929e]/8 text-[#62929e] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/12 dark:text-[#88d6e4]"
        >
          {allUploaded ? "Ready For Review" : "Upload In Progress"}
        </Badge>
      }
    >
      <ExporterPanel className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-[#1f2937] dark:text-[#edf2f7]">
              Select Assigned Order
            </h2>
            <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
              Pick an order and upload all required files.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => void reload()}
            className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
          >
            <RefreshCcw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>

        {error ? (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
            {error}
          </div>
        ) : null}

        <select
          className={selectClass}
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

        <div className="grid gap-2 text-[11px] text-[#546a7b] dark:text-[#bdcad4] md:grid-cols-3">
          <div className="rounded-xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65">
            {EXPORTER_TERMS.billOfLading}
          </div>
          <div className="rounded-xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65">
            Commercial Invoice
          </div>
          <div className="rounded-xl border border-[#546a7b]/30 bg-[#c6c5b9]/15 px-3 py-2 dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/65">
            Packing List
          </div>
        </div>
      </ExporterPanel>

      {!selectedOrderId ? (
        <ExporterEmptyState
          icon={FileText}
          title="No order selected"
          description="Select an assigned order to begin uploading shipping documents."
        />
      ) : (
        <ExporterPanel className="theme-override p-0">
          <div className="border-b border-[#546a7b]/30 px-5 py-4 dark:border-[#8fa3b1]/25 md:px-6">
            <p className="text-xs uppercase tracking-[0.16em] text-[#546a7b] dark:text-[#bdcad4]">
              Selected Order
            </p>
            <p className="mt-1 break-all font-mono text-sm text-[#1f2937] dark:text-[#edf2f7]">
              {selectedOrderId}
            </p>
            <p className="mt-1 text-xs text-[#546a7b] dark:text-[#bdcad4]">
              Upload set should include {EXPORTER_TERMS.billOfLading}, invoice, and packing list to speed approval.
            </p>
          </div>
          <div className="p-5 md:p-6">
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
        </ExporterPanel>
      )}
    </ExporterPageShell>
  );
}
