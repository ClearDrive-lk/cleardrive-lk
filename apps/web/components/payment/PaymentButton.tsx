// apps/web/components/payment/PaymentButton.tsx
// CD-206: Reusable payment button component

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { getAccessToken } from "@/lib/auth";

interface PaymentButtonProps {
  orderId: string;
  amount: number;
  currency?: string;
  className?: string;
  variant?: "default" | "outline" | "ghost" | "destructive";
  size?: "default" | "sm" | "lg" | "icon";
}

export default function PaymentButton({
  orderId,
  amount,
  currency = "LKR",
  className,
  variant = "default",
  size = "default",
}: PaymentButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prevent double-clicks (idempotency layer 1)
  const [paymentInitiated, setPaymentInitiated] = useState(false);

  const getPaymentIdempotencyKey = (currentOrderId: string): string => {
    const storageKey = `payment:idempotency:${currentOrderId}`;
    const existing = sessionStorage.getItem(storageKey);
    if (existing) return existing;

    const generated = crypto.randomUUID();
    sessionStorage.setItem(storageKey, generated);
    return generated;
  };

  const initiatePayment = async () => {
    // Check if already initiated
    if (paymentInitiated) {
      console.log("Payment already initiated");
      return;
    }

    setLoading(true);
    setError(null);
    setPaymentInitiated(true);

    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Please log in to continue payment");
      }
      const idempotencyKey = getPaymentIdempotencyKey(orderId);

      // Step 1: Initiate payment
      const initiateResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/initiate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            "Idempotency-Key": idempotencyKey,
          },
          body: JSON.stringify({
            order_id: orderId,
            idempotency_key: idempotencyKey,
          }),
        },
      );

      if (!initiateResponse.ok) {
        const errorData = await initiateResponse.json();
        throw new Error(errorData.detail || "Payment initiation failed");
      }

      const { payment_url, payhere_params } = await initiateResponse.json();

      // Step 2: Redirect to PayHere
      redirectToPayHere(payment_url, payhere_params);
    } catch (err) {
      console.error("Payment error:", err);
      setError(err instanceof Error ? err.message : "Payment failed");
      setPaymentInitiated(false);
      setLoading(false);
    }
  };

  const redirectToPayHere = (url: string, params: Record<string, string>) => {
    // Create a hidden form and submit it
    const form = document.createElement("form");
    form.method = "POST";
    form.action = url;

    // Add all PayHere parameters as hidden inputs
    Object.keys(params).forEach((key) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = key;
      input.value = params[key];
      form.appendChild(input);
    });

    // Submit form
    document.body.appendChild(form);
    form.submit();
  };

  return (
    <div className="space-y-2">
      <Button
        onClick={initiatePayment}
        disabled={loading || paymentInitiated}
        className={className}
        variant={variant}
        size={size}
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          `Pay ${currency} ${amount.toLocaleString()}`
        )}
      </Button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
