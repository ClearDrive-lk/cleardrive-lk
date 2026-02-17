"use client";

import { useState, Suspense } from "react"; // Added Suspense
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

// We move the logic into a inner component
function PaymentForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const orderId = searchParams.get("orderId");

  const handlePayment = async () => {
    if (!orderId) {
      setError("Order ID is required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const initiateResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/initiate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order_id: orderId }),
        },
      );

      if (!initiateResponse.ok) {
        const errorData = await initiateResponse.json();
        throw new Error(errorData.detail || "Failed to initiate payment");
      }

      const { payment_id } = await initiateResponse.json();

      const urlResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/generate-url`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ payment_id }),
        },
      );

      if (!urlResponse.ok) {
        const errorData = await urlResponse.json();
        throw new Error(errorData.detail || "Failed to generate payment URL");
      }

      const { payment_url, params } = await urlResponse.json();

      // Redirect to PayHere
      const form = document.createElement("form");
      form.method = "POST";
      form.action = payment_url;
      Object.keys(params).forEach((key) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = key;
        input.value = params[key];
        form.appendChild(input);
      });
      document.body.appendChild(form);
      form.submit();
    } catch (err) {
      console.error("Payment error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Payment failed. Please try again.",
      );
      setLoading(false);
    }
  };

  if (!orderId) {
    return (
      <Card className="max-w-md mx-auto bg-slate-900 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Payment Error</CardTitle>
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
        <CardTitle className="text-2xl text-white">
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

        <Button
          onClick={handlePayment}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-500 py-6 text-lg"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Processing...
            </>
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
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <Suspense fallback={<div className="text-white">Loading payment...</div>}>
        <PaymentForm />
      </Suspense>
    </div>
  );
}
