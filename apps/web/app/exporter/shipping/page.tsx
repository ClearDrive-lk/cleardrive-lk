"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { isAxiosError } from "axios";
import { Ship, RefreshCcw, Anchor, Route } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { useAssignedOrders } from "@/lib/hooks/useAssignedOrders";
import {
  ExporterPageShell,
  ExporterPanel,
} from "@/components/exporter/ExporterPageShell";
import { EXPORTER_TERMS } from "@/lib/exporter-phrases";

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

const inputClass =
  "h-11 w-full rounded-xl border border-[#546a7b]/45 bg-[#fdfdff]/80 px-3 text-sm text-[#1f2937] outline-none transition focus:border-[#62929e]/65 focus:ring-2 focus:ring-[#62929e]/20 dark:border-[#8fa3b1]/35 dark:bg-[#1a272f]/80 dark:text-[#edf2f7] dark:focus:border-[#88d6e4]/60 dark:focus:ring-[#88d6e4]/20";

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
    ["billOfLandingNumber", "Bill of lading number"],
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
    return "Invalid bill of lading number format";
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
  const completion = useMemo(() => {
    const requiredFields: Array<keyof FormState> = [
      "orderId",
      "vesselName",
      "vesselRegistration",
      "voyageNumber",
      "departurePort",
      "arrivalPort",
      "departureDate",
      "estimatedArrivalDate",
      "containerNumber",
      "billOfLandingNumber",
      "sealNumber",
      "trackingNumber",
    ];
    const filled = requiredFields.filter(
      (field) => form[field].trim().length > 0,
    );
    return Math.round((filled.length / requiredFields.length) * 100);
  }, [form]);

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
    <ExporterPageShell
      eyebrow={EXPORTER_TERMS.opsBadge}
      title="Shipping"
      accent="Details."
      description="Submit vessel route details, container references, and tracking data for each assigned export order."
      icon={Ship}
      width="narrow"
      actions={
        <Button
          variant="outline"
          onClick={() => void reload()}
          className="border-[#546a7b]/45 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
        >
          <RefreshCcw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      }
    >
      <ExporterPanel className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-[#1f2937] dark:text-[#edf2f7]">
              Assigned Order
            </h2>
            <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
              Choose the shipment order to update.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {details?.status ? (
              <Badge
                variant="outline"
                className="border-[#62929e]/25 text-[#62929e] dark:border-[#88d6e4]/35 dark:text-[#88d6e4]"
              >
                {details.status.replace(/_/g, " ")}
              </Badge>
            ) : null}
            {details?.documents_uploaded ? (
              <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-800 dark:text-emerald-200">
                Documents Uploaded
              </Badge>
            ) : null}
            <Badge
              variant="outline"
              className="border-[#62929e]/25 text-[#62929e] dark:border-[#88d6e4]/35 dark:text-[#88d6e4]"
            >
              Form {completion}% Complete
            </Badge>
          </div>
        </div>

        {ordersError ? (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
            {ordersError}
          </div>
        ) : null}

        <select
          className={inputClass}
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

        {detailsLoading ? (
          <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
            Loading shipping details...
          </p>
        ) : null}
        {detailsError ? (
          <p className="text-sm text-red-700 dark:text-red-200">
            {detailsError}
          </p>
        ) : null}

        <div className="space-y-2">
          <div className="h-2 overflow-hidden rounded-full bg-[#c6c5b9]/25 dark:bg-[#22313c]">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[#62929e] to-[#546a7b] transition-all dark:from-[#88d6e4] dark:to-[#9fb8c9]"
              style={{ width: `${completion}%` }}
            />
          </div>
          <div className="grid gap-2 text-[11px] text-[#546a7b] dark:text-[#bdcad4] md:grid-cols-3">
            <span>{EXPORTER_TERMS.containerNo}</span>
            <span>{EXPORTER_TERMS.billOfLading}</span>
            <span>{EXPORTER_TERMS.transitMilestone}</span>
          </div>
        </div>
      </ExporterPanel>

      <form onSubmit={onSubmit} className="space-y-6">
        <ExporterPanel className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-[#546a7b] dark:text-[#bdcad4]">
            <Anchor className="h-4 w-4 text-[#62929e] dark:text-[#88d6e4]" />
            Vessel and container references
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <input
              className={inputClass}
              placeholder="Vessel Name"
              value={form.vesselName}
              onChange={(e) => updateField("vesselName", e.target.value)}
            />
            <input
              className={inputClass}
              placeholder={EXPORTER_TERMS.bookingRef}
              value={form.vesselRegistration}
              onChange={(e) =>
                updateField("vesselRegistration", e.target.value)
              }
            />
            <input
              className={inputClass}
              placeholder="Voyage No."
              value={form.voyageNumber}
              onChange={(e) => updateField("voyageNumber", e.target.value)}
            />
            <input
              className={inputClass}
              placeholder={EXPORTER_TERMS.containerNo}
              value={form.containerNumber}
              onChange={(e) => updateField("containerNumber", e.target.value)}
            />
            <input
              className={inputClass}
              placeholder={EXPORTER_TERMS.billOfLading}
              value={form.billOfLandingNumber}
              onChange={(e) =>
                updateField("billOfLandingNumber", e.target.value)
              }
            />
            <input
              className={inputClass}
              placeholder={EXPORTER_TERMS.sealNo}
              value={form.sealNumber}
              onChange={(e) => updateField("sealNumber", e.target.value)}
            />
          </div>
        </ExporterPanel>

        <ExporterPanel className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-[#546a7b] dark:text-[#bdcad4]">
            <Route className="h-4 w-4 text-[#62929e] dark:text-[#88d6e4]" />
            Route and timeline details
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <input
              className={inputClass}
              placeholder={EXPORTER_TERMS.portOfLoading}
              value={form.departurePort}
              onChange={(e) => updateField("departurePort", e.target.value)}
            />
            <input
              className={inputClass}
              placeholder={EXPORTER_TERMS.portOfDischarge}
              value={form.arrivalPort}
              onChange={(e) => updateField("arrivalPort", e.target.value)}
            />
            <input
              type="date"
              className={inputClass}
              aria-label={EXPORTER_TERMS.etd}
              value={form.departureDate}
              onChange={(e) => updateField("departureDate", e.target.value)}
            />
            <input
              type="date"
              className={inputClass}
              aria-label={EXPORTER_TERMS.eta}
              value={form.estimatedArrivalDate}
              onChange={(e) =>
                updateField("estimatedArrivalDate", e.target.value)
              }
            />
            <input
              className={`${inputClass} md:col-span-2`}
              placeholder="Tracking Number / Carrier Ref"
              value={form.trackingNumber}
              onChange={(e) => updateField("trackingNumber", e.target.value)}
            />
          </div>

          {error ? (
            <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
          ) : null}
          {success ? (
            <p className="text-sm text-emerald-700 dark:text-emerald-300">
              {success}
            </p>
          ) : null}

          <Button
            type="submit"
            disabled={!canSubmit || !selectedOrderId}
            className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90"
          >
            {submitting ? "Submitting..." : "Submit Shipping Details"}
          </Button>
        </ExporterPanel>
      </form>
    </ExporterPageShell>
  );
}
