// apps/web/components/payment/PaymentButton.tsx
// CD-206: Reusable payment button component

"use client";

import { isAxiosError } from "axios";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { getAccessToken } from "@/lib/auth";
import apiClient from "@/lib/api-client";
import { useToast } from "@/lib/hooks/use-toast";

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
  const { toast } = useToast();

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

      // Step 2: Redirect to PayHere
      toast({
        title: "Redirecting to PayHere",
        description: "Complete payment to continue your order.",
      });
      redirectToPayHere(payment_url, payhere_params);
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
          "Payment failed"
        : err instanceof Error
          ? err.message
          : "Payment failed";
      setError(message);
      toast({
        title: "Payment failed",
        description: message,
        variant: "destructive",
      });
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
