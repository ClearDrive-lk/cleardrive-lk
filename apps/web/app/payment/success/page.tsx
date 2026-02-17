// apps/web/app/payment/success/page.tsx
// CD-205: Payment success page

"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id");

  useEffect(() => {
    // You can add analytics tracking here
    console.log("Payment successful for order:", orderId);
  }, [orderId]);

  return (
    <div className="container mx-auto py-8">
      <Card className="max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-10 w-10 text-green-600" />
          </div>
          <CardTitle className="text-2xl">Payment Successful!</CardTitle>
          <CardDescription>
            Your payment has been processed successfully
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {orderId && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Order ID</p>
              <p className="font-mono font-semibold">{orderId}</p>
            </div>
          )}

          <div className="space-y-2">
            <p className="text-sm text-gray-600">✅ Payment confirmed</p>
            <p className="text-sm text-gray-600">✅ Order is being processed</p>
            <p className="text-sm text-gray-600">
              ✅ Confirmation email will be sent shortly
            </p>
          </div>

          <div className="space-y-2 pt-4">
            <Button
              onClick={() => router.push("/dashboard")}
              className="w-full"
            >
              View My Orders
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push("/")}
              className="w-full"
            >
              Return to Home
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
