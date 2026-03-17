"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { isAxiosError } from "axios";
import { Ship, RefreshCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";

type FormState = {
  orderId: string;
  vesselName: string;
  vesselRegistration: string;
  voyageNumber: string;
  departurePort: string;
  arrivalPort: string;
  departureDate: string;
  estimatedArrivalDate: string;
  containerNumber: string;
  billOfLandingNumber: string;
  sealNumber: string;
  trackingNumber: string;
};

type ShippingDetails = {
  id: string;
  order_id: string;
  status?: string | null;
  documents_uploaded?: boolean;
  approved?: boolean;
  vessel_name?: string | null;
  vessel_registration?: string | null;
  voyage_number?: string | null;
  departure_port?: string | null;
  arrival_port?: string | null;
  departure_date?: string | null;
  estimated_arrival_date?: string | null;
  container_number?: string | null;
  bill_of_landing_number?: string | null;
  seal_number?: string | null;
  tracking_number?: string | null;
  created_at?: string;
  updated_at?: string;
};

const INITIAL_FORM: FormState = {
  orderId: "",
  vesselName: "",
  vesselRegistration: "",
  voyageNumber: "",
  departurePort: "",
  arrivalPort: "",
  departureDate: "",
  estimatedArrivalDate: "",
  containerNumber: "",
  billOfLandingNumber: "",
  sealNumber: "",
  trackingNumber: "",
};

function validate(form: FormState): string | null {
  const requiredFields: Array<[keyof FormState, string]> = [
    ["orderId", "Order ID"],
    ["vesselName", "Vessel name"],
    ["vesselRegistration", "Vessel registration"],
    ["voyageNumber", "Voyage number"],
    ["departurePort", "Departure port"],
    ["arrivalPort", "Arrival port"],
    ["departureDate", "Departure date"],
    ["estimatedArrivalDate", "Estimated arrival date"],
    ["containerNumber", "Container number"],
    ["billOfLandingNumber", "Bill of landing number"],
    ["sealNumber", "Seal number"],
    ["trackingNumber", "Tracking number"],
  ];

  for (const [field, label] of requiredFields) {
    if (!form[field].trim()) return `${label} is required`;
  }

  if (
    form.departurePort.trim().toLowerCase() ===
    form.arrivalPort.trim().toLowerCase()
  ) {
    return "Departure and arrival ports must be different";
  }

  const departure = new Date(form.departureDate);
  const arrival = new Date(form.estimatedArrivalDate);
  if (Number.isNaN(departure.getTime()) || Number.isNaN(arrival.getTime())) {
    return "Invalid date value";
  }
  if (arrival <= departure) {
    return "Estimated arrival date must be after departure date";
  }

  const basicCode = /^[A-Z0-9-]{5,100}$/;
  if (!basicCode.test(form.containerNumber.replace(/\s+/g, "").toUpperCase())) {
    return "Invalid container number format";
  }
  if (
    !basicCode.test(form.billOfLandingNumber.replace(/\s+/g, "").toUpperCase())
  ) {
    return "Invalid bill of landing number format";
  }

  return null;
}

export default function ExporterShippingDetailsPage() {
  const searchParams = useSearchParams();
  const orderParam = searchParams.get("orderId");
  const {
    orders,
    loading: ordersLoading,
    error: ordersError,
    reload,
  } = useAssignedOrders();

  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [selectedOrderId, setSelectedOrderId] = useState(orderParam ?? "");
  const [details, setDetails] = useState<ShippingDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedOrderId && orders.length > 0) {
      setSelectedOrderId(orders[0].id);
    }
  }, [orders, selectedOrderId]);

  useEffect(() => {
    if (orderParam) {
      setSelectedOrderId(orderParam);
    }
  }, [orderParam]);

  useEffect(() => {
    setForm((prev) => ({ ...prev, orderId: selectedOrderId }));
    if (!selectedOrderId) {
      setDetails(null);
      return;
    }

    const fetchDetails = async () => {
      setDetailsLoading(true);
      setDetailsError(null);
      try {
        const { data } = await apiClient.get<ShippingDetails>(
          `/shipping/${selectedOrderId}/details`,
        );
        setDetails(data);
        setForm((prev) => ({
          ...prev,
          orderId: selectedOrderId,
          vesselName: data.vessel_name ?? prev.vesselName,
          vesselRegistration:
            data.vessel_registration ?? prev.vesselRegistration,
          voyageNumber: data.voyage_number ?? prev.voyageNumber,
          departurePort: data.departure_port ?? prev.departurePort,
          arrivalPort: data.arrival_port ?? prev.arrivalPort,
          departureDate: data.departure_date ?? prev.departureDate,
          estimatedArrivalDate:
            data.estimated_arrival_date ?? prev.estimatedArrivalDate,
          containerNumber: data.container_number ?? prev.containerNumber,
          billOfLandingNumber:
            data.bill_of_landing_number ?? prev.billOfLandingNumber,
          sealNumber: data.seal_number ?? prev.sealNumber,
          trackingNumber: data.tracking_number ?? prev.trackingNumber,
        }));
      } catch (err) {
        if (isAxiosError(err)) {
          if (err.response?.status === 404) {
            setDetails(null);
          } else {
            setDetailsError(
              (err.response?.data as { detail?: string } | undefined)?.detail ??
                err.message,
            );
          }
        } else {
          setDetailsError("Failed to load shipping details.");
        }
      } finally {
        setDetailsLoading(false);
      }
    };

    void fetchDetails();
  }, [selectedOrderId]);

  const canSubmit = useMemo(() => !submitting, [submitting]);

  const updateField = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const validationError = validate(form);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.post(`/shipping/${form.orderId.trim()}/details`, {
        vessel_name: form.vesselName.trim(),
        vessel_registration: form.vesselRegistration.trim(),
        voyage_number: form.voyageNumber.trim(),
        departure_port: form.departurePort.trim(),
        arrival_port: form.arrivalPort.trim(),
        departure_date: form.departureDate,
        estimated_arrival_date: form.estimatedArrivalDate,
        container_number: form.containerNumber.trim(),
        bill_of_landing_number: form.billOfLandingNumber.trim(),
        seal_number: form.sealNumber.trim(),
        tracking_number: form.trackingNumber.trim(),
      });

      setSuccess("Shipping details submitted successfully.");
      void reload();
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setError(detail);
      } else {
        setError("Failed to submit shipping details.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="relative pt-16 pb-20 px-6 overflow-hidden flex-1">
      <div className="relative z-10 max-w-5xl mx-auto space-y-8">
        <div>
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743] mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
            </span>
            SHIPPING DETAILS :: EXPORTER WORKFLOW
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-white">
            SHIPPING{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
              DETAILS.
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-400 max-w-2xl">
            Submit vessel and shipment details for your assigned orders. These
            details trigger the admin review workflow.
          </p>
        </div>

        <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-white">
                Select Assigned Order
              </h2>
              <p className="text-sm text-gray-500">
                Choose an order to attach shipping details.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => void reload()}
              className="border-white/10 text-white hover:bg-white/5"
            >
              <RefreshCcw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>

          {ordersError && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {ordersError}
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <select
              className="h-11 rounded-xl bg-black/60 border border-white/10 px-3 text-sm text-white"
              value={selectedOrderId}
              onChange={(e) => setSelectedOrderId(e.target.value)}
              disabled={ordersLoading && !orders.length}
            >
              <option value="">Select an order</option>
              {orders.map((order) => (
                <option key={order.id} value={order.id}>
                  {order.id} - {order.status.replace(/_/g, " ")}
                </option>
              ))}
            </select>
            <div className="flex items-center gap-2">
              {details?.status && (
                <Badge
                  variant="outline"
                  className="border-[#FE7743]/20 text-[#FE7743]"
                >
                  {details.status.replace(/_/g, " ")}
                </Badge>
              )}
              {details?.documents_uploaded && (
                <Badge className="border-emerald-500/20 bg-emerald-500/10 text-emerald-200">
                  Documents Uploaded
                </Badge>
              )}
            </div>
          </div>

          {detailsLoading && (
            <p className="text-sm text-gray-500">Loading shipment details...</p>
          )}
          {detailsError && (
            <p className="text-sm text-red-300">{detailsError}</p>
          )}
        </div>

        <form
          onSubmit={onSubmit}
          className="space-y-6 rounded-[24px] border border-white/10 bg-[#0A0A0A] p-6"
        >
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Ship className="h-4 w-4 text-[#FE7743]" />
            Vessel & container information
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Vessel Name"
              value={form.vesselName}
              onChange={(e) => updateField("vesselName", e.target.value)}
            />
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Vessel Registration"
              value={form.vesselRegistration}
              onChange={(e) =>
                updateField("vesselRegistration", e.target.value)
              }
            />
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Voyage Number"
              value={form.voyageNumber}
              onChange={(e) => updateField("voyageNumber", e.target.value)}
            />
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Container Number"
              value={form.containerNumber}
              onChange={(e) => updateField("containerNumber", e.target.value)}
            />
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Bill of Lading Number"
              value={form.billOfLandingNumber}
              onChange={(e) =>
                updateField("billOfLandingNumber", e.target.value)
              }
            />
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Seal Number"
              value={form.sealNumber}
              onChange={(e) => updateField("sealNumber", e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Departure Port"
              value={form.departurePort}
              onChange={(e) => updateField("departurePort", e.target.value)}
            />
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              placeholder="Arrival Port"
              value={form.arrivalPort}
              onChange={(e) => updateField("arrivalPort", e.target.value)}
            />
            <input
              type="date"
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              value={form.departureDate}
              onChange={(e) => updateField("departureDate", e.target.value)}
            />
            <input
              type="date"
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm"
              value={form.estimatedArrivalDate}
              onChange={(e) =>
                updateField("estimatedArrivalDate", e.target.value)
              }
            />
            <input
              className="px-4 py-3 rounded-xl bg-black/70 border border-white/10 text-sm md:col-span-2"
              placeholder="Tracking Number"
              value={form.trackingNumber}
              onChange={(e) => updateField("trackingNumber", e.target.value)}
            />
          </div>

          {error && <div className="text-red-300 text-sm">{error}</div>}
          {success && <div className="text-green-300 text-sm">{success}</div>}

          <Button
            type="submit"
            disabled={!canSubmit || !selectedOrderId}
            className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-semibold"
          >
            {submitting ? "Submitting..." : "Submit Shipping Details"}
          </Button>
        </form>
      </div>
    </section>
  );
}
