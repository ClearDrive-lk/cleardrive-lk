// apps/web/components/payment/PaymentButton.tsx
// CD-206: Reusable payment button component

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

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
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prevent double-clicks (idempotency layer 1)
  const [paymentInitiated, setPaymentInitiated] = useState(false);

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
      // Step 1: Initiate payment
      const initiateResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/initiate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // Add auth token if you have it
            // 'Authorization': `Bearer ${getToken()}`
          },
          body: JSON.stringify({ order_id: orderId }),
        },
      );

      if (!initiateResponse.ok) {
        const errorData = await initiateResponse.json();
        throw new Error(errorData.detail || "Payment initiation failed");
      }

      const { payment_id } = await initiateResponse.json();

      // Step 2: Get PayHere URL
      const urlResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/generate-url`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ payment_id }),
        },
      );

      if (!urlResponse.ok) {
        const errorData = await urlResponse.json();
        throw new Error(errorData.detail || "Failed to generate payment URL");
      }

      const { payment_url, params } = await urlResponse.json();

      // Step 3: Redirect to PayHere
      redirectToPayHere(payment_url, params);
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
