// apps/web/components/payment/PaymentButton.tsx
// CD-206: Reusable payment button component

"use client";

import { isAxiosError } from "axios";
import { useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpRequestLoading, setOtpRequestLoading] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const { toast } = useToast();
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Prevent double-clicks (idempotency layer 1)
  const [paymentInitiated, setPaymentInitiated] = useState(false);
  const otpCode = useMemo(() => otp.join(""), [otp]);

  const getPaymentIdempotencyKey = (currentOrderId: string): string => {
    const storageKey = `payment:idempotency:${currentOrderId}`;
    const existing = sessionStorage.getItem(storageKey);
    if (existing) return existing;

    const generated = crypto.randomUUID();
    sessionStorage.setItem(storageKey, generated);
    return generated;
  };

  const initiatePayment = async () => {
    if (paymentInitiated) {
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

      toast({
        title: "Redirecting to PayHere",
        description: "Complete payment to continue your order.",
      });
      redirectToPayHere(payment_url, payhere_params);
    } catch (err) {
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

  const requestOtp = async () => {
    setOtpRequestLoading(true);
    setError(null);
    setStatusMessage(null);

    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Please log in to continue payment");
      }

      await apiClient.post(
        "/payments/request-otp",
        { order_id: orderId },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      setOtpRequested(true);
      setOtp(["", "", "", "", "", ""]);
      setStatusMessage("A payment OTP has been sent to your email.");
      inputRefs.current[0]?.focus();
    } catch (err) {
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
          "Failed to send payment OTP"
        : err instanceof Error
          ? err.message
          : "Failed to send payment OTP";
      setError(message);
    } finally {
      setOtpRequestLoading(false);
    }
  };

  const verifyOtpAndPay = async () => {
    if (otpCode.length !== 6) {
      return;
    }

    setOtpVerifying(true);
    setError(null);
    setStatusMessage(null);

    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Please log in to continue payment");
      }

      await apiClient.post(
        "/payments/verify-otp",
        { order_id: orderId, otp: otpCode },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      setStatusMessage("OTP verified. Redirecting to PayHere...");
      await initiatePayment();
    } catch (err) {
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
          "Payment OTP verification failed"
        : err instanceof Error
          ? err.message
          : "Payment OTP verification failed";
      setError(message);
    } finally {
      setOtpVerifying(false);
    }
  };

  const handleChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;
    const nextOtp = [...otp];
    nextOtp[index] = value;
    setOtp(nextOtp);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const redirectToPayHere = (url: string, params: Record<string, string>) => {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = url;

    Object.keys(params).forEach((key) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = key;
      input.value = params[key];
      form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
  };

  return (
    <div className="space-y-2">
      {!otpRequested ? (
        <Button
          onClick={() => void requestOtp()}
          disabled={otpRequestLoading}
          className={className}
          variant={variant}
          size={size}
        >
          {otpRequestLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Sending OTP...
            </>
          ) : (
            `Pay ${currency} ${amount.toLocaleString()}`
          )}
        </Button>
      ) : (
        <>
          <div className="flex gap-2">
            {otp.map((digit, index) => (
              <Input
                key={index}
                ref={(el) => {
                  inputRefs.current[index] = el;
                }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                className="h-10 w-10 text-center font-mono"
              />
            ))}
          </div>
          <Button
            onClick={() => void verifyOtpAndPay()}
            disabled={
              loading ||
              paymentInitiated ||
              otpVerifying ||
              otpCode.length !== 6
            }
            className={className}
            variant={variant}
            size={size}
          >
            {loading || otpVerifying ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              "Verify OTP and Pay"
            )}
          </Button>
        </>
      )}
      {statusMessage && (
        <p className="text-sm text-emerald-600">{statusMessage}</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
