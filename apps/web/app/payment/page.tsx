"use client";

import { isAxiosError } from "axios";
import { useEffect, useState, Suspense } from "react"; // Added Suspense
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { getAccessToken } from "@/lib/auth";
import apiClient from "@/lib/api-client";
import { useKycStatus } from "@/lib/hooks/useKycStatus";
import { useToast } from "@/lib/hooks/use-toast";

// We move the logic into a inner component
function PaymentForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const { isApproved, loading: kycLoading, normalizedStatus } = useKycStatus();

  const orderId = searchParams.get("orderId");
  const [resubmissionError, setResubmissionError] = useState<string | null>(
    null,
  );

  useEffect(() => {
    if (!orderId) return;
    const submittedAt = sessionStorage.getItem(`payment:submitted:${orderId}`);
    if (!submittedAt) return;
    setResubmissionError(
      "This payment was already submitted once. Re-submitting may create a duplicate attempt. Check your order status before trying again.",
    );
  }, [orderId]);

  const getPaymentIdempotencyKey = (currentOrderId: string): string => {
    const storageKey = `payment:idempotency:${currentOrderId}`;
    const existing = sessionStorage.getItem(storageKey);
    if (existing) return existing;

    const generated = crypto.randomUUID();
    sessionStorage.setItem(storageKey, generated);
    return generated;
  };

  const handlePayment = async () => {
    if (!orderId) {
      setError("Order ID is required");
      return;
    }
    if (kycLoading) {
      return;
    }
    if (!isApproved) {
      const message =
        normalizedStatus === null
          ? "KYC verification required before payment."
          : `KYC status is ${normalizedStatus}. Only approved users can proceed to payment.`;
      setError(message);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Please log in to continue payment");
      }
      const idempotencyKey = getPaymentIdempotencyKey(orderId);

      const { data } = await apiClient.post(
        "/payments/initiate",
        {
          order_id: orderId,
          idempotency_key: idempotencyKey,
        },
        {
          headers: {
            "Idempotency-Key": idempotencyKey,
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const { payment_url, payhere_params } = data as {
        payment_url: string;
        payhere_params: Record<string, string>;
      };

      sessionStorage.setItem(
        `payment:submitted:${orderId}`,
        new Date().toISOString(),
      );

      // Redirect to PayHere
      toast({
        title: "Redirecting to PayHere",
        description: "Complete payment to continue your order.",
      });
      const form = document.createElement("form");
      form.method = "POST";
      form.action = payment_url;
      Object.keys(payhere_params).forEach((key) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = key;
        input.value = payhere_params[key];
        form.appendChild(input);
      });
      document.body.appendChild(form);
      form.submit();
    } catch (err) {
      console.error("Payment error:", err);
      const message = isAxiosError(err)
        ? (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.detail ||
          (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.message ||
          err.message ||
          "Payment failed. Please try again."
        : err instanceof Error
          ? err.message
          : "Payment failed. Please try again.";
      setError(message);
      toast({
        title: "Payment failed",
        description: message,
        variant: "destructive",
      });
      setLoading(false);
    }
  };

  if (!orderId) {
    return (
      <Card className="max-w-md mx-auto bg-slate-900 border-slate-700">
        <CardHeader>
          <CardTitle className="text-[#393d3f]">Payment Error</CardTitle>
          <CardDescription>No order ID provided</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => router.push("/")} className="w-full">
            Return to Home
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="max-w-md mx-auto bg-slate-900 border-slate-800 shadow-2xl">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl text-[#393d3f]">
          Complete Your Payment
        </CardTitle>
        <CardDescription className="text-slate-400">
          Order ID: {orderId}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        {resubmissionError && (
          <div className="bg-amber-500/10 border border-amber-500/40 text-amber-300 px-4 py-3 rounded text-sm">
            {resubmissionError}
          </div>
        )}

        {!kycLoading && !isApproved && (
          <div className="bg-amber-500/10 border border-amber-500/40 text-amber-300 px-4 py-3 rounded text-sm">
            KYC must be approved before payment.
            <a
              href="/dashboard/kyc"
              className="ml-2 font-semibold text-white underline underline-offset-4"
            >
              Open KYC
            </a>
            {normalizedStatus ? ` Current status: ${normalizedStatus}.` : ""}
          </div>
        )}

        <Button
          onClick={handlePayment}
          disabled={loading || kycLoading || !isApproved}
          className="w-full bg-blue-600 hover:bg-blue-500 py-6 text-lg"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Processing...
            </>
          ) : kycLoading ? (
            "Checking KYC..."
          ) : !isApproved ? (
            "KYC Approval Required"
          ) : (
            "Proceed to Payment"
          )}
        </Button>

        <Button
          variant="outline"
          onClick={() => router.back()}
          className="w-full border-slate-700 text-slate-300 hover:bg-slate-800"
          disabled={loading}
        >
          Cancel
        </Button>
      </CardContent>
    </Card>
  );
}

// Main page component with Suspense wrapper
export default function PaymentPage() {
  return (
    <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center p-4">
      <Suspense
        fallback={<div className="text-[#393d3f]">Loading payment...</div>}
      >
        <PaymentForm />
      </Suspense>
    </div>
  );
}
