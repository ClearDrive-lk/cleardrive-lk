"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, CheckCircle2, Clock, Copy, RefreshCcw } from "lucide-react";

import AuthGuard from "@/components/auth/AuthGuard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { OrderTimeline } from "@/components/ui/OrderTimeline";
import ThemeToggle from "@/components/ui/theme-toggle";
import PaymentButton from "@/components/payment/PaymentButton";
import apiClient from "@/lib/api-client";
import { getOrderStatusBadgeClass } from "@/lib/order-status-badge";
import { mapBackendVehicle } from "@/lib/vehicle-mapper";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import type { Vehicle } from "@/types/vehicle";
import { useToast } from "@/lib/hooks/use-toast";

interface OrderDetail {
  id: string;
  status: string;
  payment_status: string;
  total_cost_lkr: number | string | null;
  created_at: string;
  vehicle_id?: string;
  phone?: string;
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [vehicleLoading, setVehicleLoading] = useState(false);
  const [vehicleError, setVehicleError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);
  const { toast } = useToast();

  const loadOrder = useCallback(
    async ({ silent = false }: { silent?: boolean } = {}) => {
      if (!id) return;
      if (!silent) {
        setLoading(true);
        setError(null);
      }

      try {
        const { data } = await apiClient.get<OrderDetail>(`/orders/${id}`);
        setOrder(data);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load order details.";
        setError(message);
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [id],
  );

  useEffect(() => {
    void loadOrder();
  }, [loadOrder]);

  useEffect(() => {
    const loadVehicle = async () => {
      if (!order?.vehicle_id) {
        setVehicle(null);
        return;
      }
      setVehicleLoading(true);
      setVehicleError(null);
      try {
        const { data } = await apiClient.get(`/vehicles/${order.vehicle_id}`);
        setVehicle(mapBackendVehicle(data));
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Failed to load vehicle details.";
        setVehicleError(message);
      } finally {
        setVehicleLoading(false);
      }
    };

    void loadVehicle();
  }, [order?.vehicle_id]);

  const totalAmount = useMemo(() => {
    if (!order?.total_cost_lkr) return null;
    const numeric = Number(order.total_cost_lkr);
    return Number.isFinite(numeric) ? numeric : null;
  }, [order]);

  const canPay =
    order?.status === "CREATED" && order.payment_status === "PENDING";
  const canCancel =
    order?.status === "CREATED" && order.payment_status === "PENDING";
  const paymentStatus = order?.payment_status ?? "PENDING";

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

  const handleCopyOrderId = async () => {
    if (!order?.id || typeof navigator === "undefined") return;
    try {
      await navigator.clipboard.writeText(order.id);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  const handleCancelOrder = async () => {
    if (!order?.id) return;
    setCancelLoading(true);
    try {
      await apiClient.patch(`/orders/${order.id}/cancel`);
      toast({
        title: "Order cancelled",
        description: "Your order has been cancelled successfully.",
        variant: "success",
      });
      setShowCancelConfirm(false);
      void loadOrder({ silent: true });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to cancel order.";
      toast({
        title: "Cancellation failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setCancelLoading(false);
    }
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="cd-container h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2"
            >
              <BrandMark className="h-8 w-8 rounded-md border border-[#62929e]/20 bg-[#62929e]/10" />
              <BrandWordmark />
            </Link>
            <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b]">
              <Link
                href="/dashboard"
                className="hover:text-[#393d3f] transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/dashboard/orders"
                className="text-[#393d3f] transition-colors flex items-center gap-2"
              >
                Orders
                <Badge
                  variant="outline"
                  className="text-[10px] border-[#62929e]/20 text-[#62929e] h-4 px-1"
                >
                  ACTIVE
                </Badge>
              </Link>
              <Link
                href="/dashboard/vehicles"
                className="hover:text-[#393d3f] transition-colors"
              >
                Vehicles
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
            </div>
          </div>
        </nav>

        <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/5 rounded-[100%] blur-[120px] pointer-events-none" />

        <main className="relative z-10 flex-1 py-12">
          <div className="cd-container-narrow space-y-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <Link
                  href="/dashboard/orders"
                  className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-[#546a7b] hover:text-[#393d3f]"
                >
                  <ArrowLeft className="h-4 w-4" /> Back to Orders
                </Link>
                <h1 className="mt-3 text-3xl md:text-4xl font-bold text-[#393d3f]">
                  Order Tracking
                </h1>
                <p className="text-sm text-[#546a7b]">
                  Review payment status and shipment milestones in one place.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void loadOrder()}
                className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
              >
                <RefreshCcw className="mr-2 h-4 w-4" /> Refresh
              </Button>
            </div>

            {order && (
              <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
                {paymentStatus === "COMPLETED" ? (
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm text-emerald-800 dark:text-emerald-300">
                      <CheckCircle2 className="h-4 w-4" />
                      Payment confirmed. Shipment processing is underway.
                    </div>
                    <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-800 dark:text-emerald-200">
                      Paid
                    </Badge>
                  </div>
                ) : paymentStatus === "FAILED" ? (
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="text-sm text-red-700 dark:text-red-200">
                      Payment failed. Please retry to continue processing.
                    </div>
                    <Button
                      asChild
                      className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
                    >
                      <Link href={`/payment?orderId=${order.id}`}>
                        Retry Payment
                      </Link>
                    </Button>
                  </div>
                ) : (
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="text-sm text-amber-800 dark:text-amber-200">
                      Payment required to move this order forward.
                    </div>
                    <Button
                      asChild
                      className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
                    >
                      <Link href="#payment-action">Complete Payment</Link>
                    </Button>
                  </div>
                )}
              </div>
            )}

            {loading ? (
              <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-10 text-center text-[#546a7b]">
                Loading order...
              </div>
            ) : error ? (
              <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-200">
                {error}
              </div>
            ) : order ? (
              <div className="grid gap-8 lg:grid-cols-[360px_minmax(0,1fr)]">
                <div className="space-y-4">
                  <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.25em] text-[#546a7b]">
                          Order ID
                        </p>
                        <p className="mt-2 font-mono text-sm text-[#393d3f]">
                          {order.id}
                        </p>
                        <button
                          type="button"
                          onClick={handleCopyOrderId}
                          className="mt-2 inline-flex items-center gap-2 text-xs text-[#546a7b] hover:text-[#393d3f]"
                        >
                          <Copy className="h-3 w-3" />
                          {copied ? "Copied" : "Copy ID"}
                        </button>
                      </div>
                      <Badge className={getOrderStatusBadgeClass(order.status)}>
                        {order.status.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <div className="mt-4 flex items-center gap-2 text-xs text-[#546a7b]">
                      <Clock className="h-3 w-3" />
                      Created {new Date(order.created_at).toLocaleString()}
                    </div>
                    <div className="mt-4 rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
                      <div className="flex items-center justify-between text-sm text-[#546a7b]">
                        <span>Total Cost</span>
                        <span className="font-semibold text-[#393d3f]">
                          {formatLkr(order.total_cost_lkr)}
                        </span>
                      </div>
                      <div className="mt-2 text-xs text-[#546a7b]">
                        Payment status:{" "}
                        {order.payment_status.replace(/_/g, " ")}
                      </div>
                    </div>

                    <div className="mt-4 text-xs text-[#546a7b]">
                      Shipping address is stored securely and encrypted.
                    </div>
                  </div>

                  <div id="payment-action">
                    {canPay && totalAmount ? (
                      <PaymentButton
                        orderId={order.id}
                        amount={totalAmount}
                        className="w-full bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
                      />
                    ) : (
                      <Button
                        disabled
                        className="w-full bg-[#c6c5b9]/20 text-[#546a7b] border border-[#546a7b]/65"
                      >
                        Payment unavailable for this status
                      </Button>
                    )}
                  </div>

                  <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
                    <h3 className="text-sm font-semibold text-[#393d3f]">
                      Vehicle Summary
                    </h3>
                    {vehicleLoading ? (
                      <div className="mt-3 text-xs text-[#546a7b]">
                        Loading vehicle details...
                      </div>
                    ) : vehicleError ? (
                      <div className="mt-3 text-xs text-red-700 dark:text-red-200">
                        {vehicleError}
                      </div>
                    ) : vehicle ? (
                      <div className="mt-3 flex gap-4">
                        <div className="relative h-20 w-28 overflow-hidden rounded-lg border border-[#546a7b]/65 bg-[#fdfdff]">
                          {vehicle.imageUrl ? (
                            <Image
                              src={vehicle.imageUrl}
                              alt={`${vehicle.make} ${vehicle.model}`}
                              fill
                              className="object-cover"
                            />
                          ) : (
                            <div className="h-full w-full bg-[#c6c5b9]/20" />
                          )}
                        </div>
                        <div className="flex-1 text-sm text-[#546a7b]">
                          <p className="text-[#393d3f] font-semibold">
                            {vehicle.year} {vehicle.make} {vehicle.model}
                          </p>
                          <p className="text-xs text-[#546a7b]">
                            Lot #{vehicle.lotNumber} · {vehicle.mileage} km
                          </p>
                          <p className="text-xs text-[#546a7b]">
                            Est. Landed:{" "}
                            {formatLkr(vehicle.estimatedLandedCostLKR)}
                          </p>
                          <Button
                            asChild
                            size="sm"
                            variant="outline"
                            className="mt-2 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                          >
                            <Link href={`/dashboard/vehicles/${vehicle.id}`}>
                              View Vehicle
                            </Link>
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-3 text-xs text-[#546a7b]">
                        Vehicle details unavailable.
                      </div>
                    )}
                  </div>

                  <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-xs text-[#546a7b]">
                    Vehicle ID: {order.vehicle_id ?? "N/A"}
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Button
                      asChild
                      variant="outline"
                      className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                    >
                      <Link href={`/payment?orderId=${order.id}`}>
                        Open Payment Page
                      </Link>
                    </Button>
                    <Button
                      asChild
                      variant="outline"
                      className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                    >
                      <Link href={`/dashboard/orders/${order.id}/confirmation`}>
                        Order Confirmation
                      </Link>
                    </Button>
                  </div>

                  {canCancel && (
                    <div className="rounded-[24px] border border-red-500/20 bg-red-500/10 p-4 text-xs text-red-800 dark:text-red-200">
                      <p className="text-sm font-semibold text-red-900 dark:text-red-100">
                        Cancel this order?
                      </p>
                      <p className="mt-1 text-xs text-red-800/80 dark:text-red-200/80">
                        You can cancel before payment is completed. This will
                        release the vehicle back to inventory.
                      </p>
                      <div className="mt-3 flex flex-wrap gap-3">
                        <Button
                          variant="outline"
                          className="border-red-500/40 text-red-800 hover:bg-red-500/10 dark:text-red-100"
                          onClick={() => setShowCancelConfirm((prev) => !prev)}
                        >
                          {showCancelConfirm
                            ? "Hide Confirmation"
                            : "Cancel Order"}
                        </Button>
                      </div>
                      {showCancelConfirm && (
                        <div className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-800 dark:text-red-100">
                          <p>Are you sure? This action cannot be undone.</p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <Button
                              onClick={handleCancelOrder}
                              disabled={cancelLoading}
                              className="bg-red-500 text-[#393d3f] hover:bg-red-400"
                            >
                              {cancelLoading
                                ? "Cancelling..."
                                : "Confirm Cancel"}
                            </Button>
                            <Button
                              variant="outline"
                              className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                              onClick={() => setShowCancelConfirm(false)}
                            >
                              Keep Order
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <OrderTimeline
                    orderId={order.id}
                    onTimelineUpdate={() => {
                      void loadOrder({ silent: true });
                    }}
                  />
                </div>
              </div>
            ) : null}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
