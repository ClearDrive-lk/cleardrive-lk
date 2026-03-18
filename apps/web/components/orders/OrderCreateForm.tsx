"use client";

import { useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2, MapPin, Phone, Shield } from "lucide-react";

import apiClient from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/lib/hooks/use-toast";

interface OrderCreateFormProps {
  vehicleId: string;
  estimatedTotalLkr?: number | null;
}

type CreatedOrder = {
  id: string;
  status: string;
  payment_status: string;
  total_cost_lkr: number | string | null;
};

export default function OrderCreateForm({
  vehicleId,
  estimatedTotalLkr,
}: OrderCreateFormProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [shippingAddress, setShippingAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdOrder, setCreatedOrder] = useState<CreatedOrder | null>(null);

  const trimmedAddress = shippingAddress.trim();
  const trimmedPhone = phone.trim();

  const isAddressValid = trimmedAddress.length >= 10;
  const isPhoneValid = trimmedPhone.length >= 7;

  const canSubmit = useMemo(
    () => Boolean(vehicleId) && isAddressValid && isPhoneValid && !submitting,
    [vehicleId, isAddressValid, isPhoneValid, submitting],
  );

  const formatLkr = (value: number | string | null | undefined) => {
    if (value === null || value === undefined) return "N/A";
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "N/A";
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      maximumSignificantDigits: 3,
    }).format(numeric);
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      setError("Please provide a valid shipping address and phone number.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const { data } = await apiClient.post<CreatedOrder>("/orders", {
        vehicle_id: vehicleId,
        shipping_address: trimmedAddress,
        phone: trimmedPhone,
      });

      setCreatedOrder(data);
      toast({
        title: "Order created",
        description:
          "Your order has been saved. Proceed to payment when ready.",
        variant: "success",
      });
    } catch (err) {
      if (isAxiosError(err)) {
        const message =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          "Unable to create the order. Please try again.";
        setError(message);
        toast({
          title: "Order creation failed",
          description: message,
          variant: "destructive",
        });
      } else {
        setError("Unable to create the order. Please try again.");
        toast({
          title: "Order creation failed",
          description: "Unable to create the order. Please try again.",
          variant: "destructive",
        });
      }
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (!createdOrder) return;
    const timeout = window.setTimeout(() => {
      router.push(`/dashboard/orders/${createdOrder.id}/confirmation`);
    }, 2000);
    return () => window.clearTimeout(timeout);
  }, [createdOrder, router]);

  return (
    <Card className="border-[#546a7b]/65 bg-[#fdfdff]">
      <CardHeader className="space-y-2">
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[#62929e]">
          <Shield className="h-4 w-4" /> Secure Checkout
        </div>
        <CardTitle className="text-xl text-[#393d3f]">Create Your Order</CardTitle>
        <p className="text-sm text-[#546a7b]">
          Add your delivery details to reserve this vehicle. Your address is
          encrypted at rest.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {createdOrder ? (
          <div className="space-y-4">
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-emerald-200">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <CheckCircle2 className="h-4 w-4" /> Order Created Successfully
              </div>
              <div className="mt-2 text-xs text-emerald-100/80">
                Order ID: <span className="font-mono">{createdOrder.id}</span>
              </div>
              <div className="mt-2 text-xs text-emerald-100/80">
                Status: {createdOrder.status.replace(/_/g, " ")}
              </div>
            </div>

            <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-sm text-[#546a7b]">
              <div className="flex items-center justify-between">
                <span>Estimated Total</span>
                <span className="font-semibold text-[#393d3f]">
                  {formatLkr(createdOrder.total_cost_lkr)}
                </span>
              </div>
              <div className="mt-2 text-xs text-[#546a7b]">
                Payment status: {createdOrder.payment_status.replace(/_/g, " ")}
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                asChild
                className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
              >
                <Link href={`/payment?orderId=${createdOrder.id}`}>
                  Pay Now
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
              >
                <Link
                  href={`/dashboard/orders/${createdOrder.id}/confirmation`}
                >
                  View Confirmation
                </Link>
              </Button>
            </div>
            <p className="text-xs text-[#546a7b]">
              Redirecting to confirmation in 2 seconds. You can always track
              progress in the Orders dashboard.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[#546a7b]">
                Shipping Address
              </label>
              <div className="relative">
                <MapPin className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-[#546a7b]" />
                <textarea
                  value={shippingAddress}
                  onChange={(event) => setShippingAddress(event.target.value)}
                  placeholder="House no, street, city, postal code"
                  className="min-h-[120px] w-full rounded-md border border-[#546a7b]/65 bg-transparent px-10 py-2 text-sm text-[#393d3f] placeholder:text-[#546a7b] focus:border-[#62929e] focus:outline-none focus:ring-2 focus:ring-[#62929e]/30"
                />
              </div>
              {!isAddressValid && trimmedAddress.length > 0 && (
                <p className="text-xs text-amber-300">
                  Please enter at least 10 characters.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[#546a7b]">
                Contact Number
              </label>
              <div className="relative">
                <Phone className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#546a7b]" />
                <Input
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="07X XXX XXXX"
                  type="tel"
                  className="pl-10 bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] focus:border-[#62929e]"
                />
              </div>
              {!isPhoneValid && trimmedPhone.length > 0 && (
                <p className="text-xs text-amber-300">
                  Please enter a valid phone number.
                </p>
              )}
            </div>

            <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-sm text-[#546a7b]">
              <div className="flex items-center justify-between">
                <span>Estimated Total</span>
                <span className="font-semibold text-[#393d3f]">
                  {formatLkr(estimatedTotalLkr)}
                </span>
              </div>
              <div className="mt-2 text-xs text-[#546a7b]">
                Final pricing is confirmed after Customs valuation.
              </div>
            </div>

            {error && (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                {error}
              </div>
            )}

            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="w-full bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold h-11"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Order...
                </>
              ) : (
                "Create Order"
              )}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}

