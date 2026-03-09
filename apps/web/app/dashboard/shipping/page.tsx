"use client";

import { useMemo, useState } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import { apiClient } from "@/lib/api-client";
import Link from "next/link";
import { isAxiosError } from "axios";

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

  if (form.departurePort.trim().toLowerCase() === form.arrivalPort.trim().toLowerCase()) {
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
  if (!basicCode.test(form.billOfLandingNumber.replace(/\s+/g, "").toUpperCase())) {
    return "Invalid bill of landing number format";
  }

  return null;
}

export default function ShippingDetailsPage() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ?? err.message;
        setError(detail);
      } else {
        setError("Failed to submit shipping details.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#050505] text-white p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Shipping Details Submission</h1>
              <p className="text-gray-400 mt-1">
                Submit vessel and shipment details for your assigned order.
              </p>
            </div>
            <Link href="/dashboard/orders" className="text-[#FE7743] hover:underline">
              Back to Orders
            </Link>
          </div>

          <form onSubmit={onSubmit} className="space-y-4 bg-[#0A0A0A] border border-white/10 rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Order ID (UUID)"
                value={form.orderId}
                onChange={(e) => updateField("orderId", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Vessel Name"
                value={form.vesselName}
                onChange={(e) => updateField("vesselName", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Vessel Registration"
                value={form.vesselRegistration}
                onChange={(e) => updateField("vesselRegistration", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Voyage Number"
                value={form.voyageNumber}
                onChange={(e) => updateField("voyageNumber", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Departure Port"
                value={form.departurePort}
                onChange={(e) => updateField("departurePort", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Arrival Port"
                value={form.arrivalPort}
                onChange={(e) => updateField("arrivalPort", e.target.value)}
              />
              <input
                type="date"
                className="px-3 py-2 rounded bg-black border border-white/15"
                value={form.departureDate}
                onChange={(e) => updateField("departureDate", e.target.value)}
              />
              <input
                type="date"
                className="px-3 py-2 rounded bg-black border border-white/15"
                value={form.estimatedArrivalDate}
                onChange={(e) => updateField("estimatedArrivalDate", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Container Number"
                value={form.containerNumber}
                onChange={(e) => updateField("containerNumber", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Bill of Landing Number"
                value={form.billOfLandingNumber}
                onChange={(e) => updateField("billOfLandingNumber", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Seal Number"
                value={form.sealNumber}
                onChange={(e) => updateField("sealNumber", e.target.value)}
              />
              <input
                className="px-3 py-2 rounded bg-black border border-white/15"
                placeholder="Tracking Number"
                value={form.trackingNumber}
                onChange={(e) => updateField("trackingNumber", e.target.value)}
              />
            </div>

            {error && <div className="text-red-300 text-sm">{error}</div>}
            {success && <div className="text-green-300 text-sm">{success}</div>}

            <button
              type="submit"
              disabled={!canSubmit}
              className="px-4 py-2 rounded bg-[#FE7743] text-black font-semibold disabled:opacity-60"
            >
              {submitting ? "Submitting..." : "Submit Shipping Details"}
            </button>
          </form>
        </div>
      </div>
    </AuthGuard>
  );
}
