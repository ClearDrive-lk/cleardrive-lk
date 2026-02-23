"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { z } from "zod";
import { Resolver, useForm } from "react-hook-form";
import { AnimatePresence, motion } from "framer-motion";
import { Lock, ChevronLeft, ChevronRight, CheckCircle2 } from "lucide-react";
import axios from "axios";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";
import {
  buildPayHereOrderDataFromParams,
  submitPayHereForm,
} from "@/lib/payhere";

const orderWizardSchema = z.object({
  vehicleId: z.string().min(1, "Vehicle is required"),
  shippingDetails: z.object({
    fullName: z.string().min(2, "Full name is required"),
    address: z.string().min(5, "Address is required"),
    nicOrPassport: z.string().min(4, "NIC or Passport is required"),
    phoneNumber: z.string().min(7, "Phone number is required"),
  }),
});

export type OrderWizardValues = z.infer<typeof orderWizardSchema>;

export interface OrderWizardVehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  imageUrl: string;
  thumbnails?: string[];
  lotNumber?: string;
  cifPriceLkr: number;
}

export interface OrderWizardPayload extends OrderWizardValues {
  financials: {
    cifPrice: number;
    estimatedCustomsDuty: number;
    clearingAndPortCharges: number;
    clearDriveServiceFee: number;
    totalLandedCost: number;
  };
}

interface OrderWizardProps {
  vehicle: OrderWizardVehicle;
  className?: string;
}

const STEP_TITLES = [
  "Vehicle Confirmation",
  "Secure Shipping",
  "Transparency Receipt",
] as const;

const CLEARING_AND_PORT_CHARGES = 50_000;
const CLEARDRIVE_SERVICE_FEE = 100_000;

const formatLkr = (amount: number) =>
  new Intl.NumberFormat("en-LK", {
    style: "currency",
    currency: "LKR",
    maximumFractionDigits: 0,
  }).format(amount);

const orderWizardResolver: Resolver<OrderWizardValues> = async (values) => {
  const parsed = orderWizardSchema.safeParse(values);
  if (parsed.success) {
    return {
      values: parsed.data as OrderWizardValues,
      errors: {},
    };
  }

  const fieldErrors: Record<string, { type: string; message: string }> = {};
  for (const issue of parsed.error.issues) {
    const path = issue.path.join(".");
    if (!path || fieldErrors[path]) continue;
    fieldErrors[path] = {
      type: "zod",
      message: issue.message,
    };
  }

  return {
    values: {} as never,
    errors: fieldErrors as never,
  };
};

export function OrderWizard({ vehicle, className }: OrderWizardProps) {
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState<1 | -1>(1);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    trigger,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<OrderWizardValues>({
    resolver: orderWizardResolver,
    defaultValues: {
      vehicleId: vehicle.id,
      shippingDetails: {
        fullName: "",
        address: "",
        nicOrPassport: "",
        phoneNumber: "",
      },
    },
  });

  useEffect(() => {
    setValue("vehicleId", vehicle.id, { shouldValidate: true });
  }, [setValue, vehicle.id]);

  const thumbnails = useMemo(() => {
    const images = [vehicle.imageUrl, ...(vehicle.thumbnails ?? [])].filter(
      Boolean,
    ) as string[];
    return Array.from(new Set(images));
  }, [vehicle.imageUrl, vehicle.thumbnails]);

  const cifPrice = vehicle.cifPriceLkr;
  const estimatedCustomsDuty = Math.round(cifPrice * 0.3);
  const totalLandedCost =
    cifPrice +
    estimatedCustomsDuty +
    CLEARING_AND_PORT_CHARGES +
    CLEARDRIVE_SERVICE_FEE;

  const nextStep = async () => {
    if (step === 1) {
      const isStepValid = await trigger("shippingDetails");
      if (!isStepValid) return;
    }

    setDirection(1);
    setStep((previousStep) =>
      Math.min(previousStep + 1, STEP_TITLES.length - 1),
    );
  };

  const previousStep = () => {
    setDirection(-1);
    setStep((currentStep) => Math.max(currentStep - 1, 0));
  };

  const submitOrder = handleSubmit(async (values) => {
    const payload: OrderWizardPayload = {
      ...values,
      financials: {
        cifPrice,
        estimatedCustomsDuty,
        clearingAndPortCharges: CLEARING_AND_PORT_CHARGES,
        clearDriveServiceFee: CLEARDRIVE_SERVICE_FEE,
        totalLandedCost,
      },
    };

    try {
      setSubmitError(null);
      const response = await apiClient.post("/orders", payload);
      const responseData = response.data ?? {};
      const paymentUrl = responseData.payment_url;
      const params = responseData.params;

      if (!paymentUrl || !params || typeof params !== "object") {
        throw new Error(
          "Payment initialization failed. Invalid server response.",
        );
      }

      const { orderData, hash } = buildPayHereOrderDataFromParams(params);
      if (!hash) {
        throw new Error("Payment initialization failed. Missing PayHere hash.");
      }

      submitPayHereForm(orderData, hash, paymentUrl);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiMessage =
          (
            error.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.detail ??
          (
            error.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.message;

        setSubmitError(
          apiMessage || error.message || "Failed to create order.",
        );
        return;
      }

      setSubmitError(
        error instanceof Error ? error.message : "Failed to create order.",
      );
    }
  });

  return (
    <form onSubmit={submitOrder} className={cn("w-full", className)}>
      <Card className="border-white/10 bg-[#0D0D0D] text-white">
        <CardHeader className="space-y-5">
          <CardTitle className="text-2xl">Create Your Import Order</CardTitle>

          <div className="grid grid-cols-3 gap-3">
            {STEP_TITLES.map((title, index) => {
              const isCompleted = step > index;
              const isActive = step === index;

              return (
                <div
                  key={title}
                  className={cn(
                    "rounded-md border px-3 py-2 text-xs md:text-sm transition-colors",
                    isCompleted && "border-emerald-500/30 bg-emerald-500/10",
                    isActive && "border-[#FE7743]/40 bg-[#FE7743]/10",
                    !isCompleted &&
                      !isActive &&
                      "border-white/10 bg-black/20 text-zinc-400",
                  )}
                >
                  <p className="font-semibold">{index + 1}</p>
                  <p className="truncate">{title}</p>
                </div>
              );
            })}
          </div>
        </CardHeader>

        <CardContent className="overflow-hidden">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={step}
              initial={{ opacity: 0, x: direction > 0 ? 72 : -72 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: direction > 0 ? -72 : 72 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
            >
              {step === 0 ? (
                <section className="space-y-5">
                  <h3 className="text-lg font-semibold">
                    Vehicle Confirmation
                  </h3>
                  <div className="rounded-lg border border-white/10 bg-black/30 p-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <div className="relative aspect-[16/10] overflow-hidden rounded-md border border-white/10">
                          <Image
                            src={thumbnails[0] ?? vehicle.imageUrl}
                            alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
                            fill
                            className="object-cover"
                            sizes="(max-width: 768px) 100vw, 420px"
                          />
                        </div>
                        <div className="flex gap-2 overflow-x-auto pb-1">
                          {thumbnails.map((thumbnail, index) => (
                            <div
                              key={`${thumbnail}-${index}`}
                              className="relative h-16 w-24 shrink-0 overflow-hidden rounded border border-white/10"
                            >
                              <Image
                                src={thumbnail}
                                alt={`Vehicle thumbnail ${index + 1}`}
                                fill
                                className="object-cover"
                                sizes="96px"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <p className="text-xl font-semibold">
                          {vehicle.year} {vehicle.make} {vehicle.model}
                        </p>
                        {vehicle.lotNumber ? (
                          <p className="text-sm text-zinc-400">
                            Lot Number:{" "}
                            <span className="text-zinc-200">
                              {vehicle.lotNumber}
                            </span>
                          </p>
                        ) : null}
                        <Separator className="bg-white/10" />
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center justify-between text-zinc-400">
                            <span>CIF Price (Base vehicle price)</span>
                            <span className="font-semibold text-white">
                              {formatLkr(cifPrice)}
                            </span>
                          </div>
                          <p className="text-xs text-zinc-500">
                            Confirm this vehicle summary before continuing with
                            shipping.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </section>
              ) : null}

              {step === 1 ? (
                <section className="space-y-5">
                  <div className="flex items-center gap-2 text-sm text-emerald-300">
                    <Lock className="h-4 w-4" />
                    <span>Encrypted & Secured for Sri Lanka Customs</span>
                  </div>
                  <h3 className="text-lg font-semibold">Secure Shipping</h3>

                  <div className="grid gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input
                        id="fullName"
                        {...register("shippingDetails.fullName")}
                        className="border-white/15 bg-black/30"
                        placeholder="Full name as per NIC/Passport"
                      />
                      {errors.shippingDetails?.fullName ? (
                        <p className="text-xs text-red-400">
                          {errors.shippingDetails.fullName.message}
                        </p>
                      ) : null}
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="address">Address</Label>
                      <Input
                        id="address"
                        {...register("shippingDetails.address")}
                        className="border-white/15 bg-black/30"
                        placeholder="Shipping address in Sri Lanka"
                      />
                      {errors.shippingDetails?.address ? (
                        <p className="text-xs text-red-400">
                          {errors.shippingDetails.address.message}
                        </p>
                      ) : null}
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="grid gap-2">
                        <Label htmlFor="nicOrPassport">NIC or Passport</Label>
                        <Input
                          id="nicOrPassport"
                          {...register("shippingDetails.nicOrPassport")}
                          className="border-white/15 bg-black/30"
                          placeholder="NIC / Passport number"
                        />
                        {errors.shippingDetails?.nicOrPassport ? (
                          <p className="text-xs text-red-400">
                            {errors.shippingDetails.nicOrPassport.message}
                          </p>
                        ) : null}
                      </div>

                      <div className="grid gap-2">
                        <Label htmlFor="phoneNumber">Phone Number</Label>
                        <Input
                          id="phoneNumber"
                          {...register("shippingDetails.phoneNumber")}
                          className="border-white/15 bg-black/30"
                          placeholder="+94 XX XXX XXXX"
                        />
                        {errors.shippingDetails?.phoneNumber ? (
                          <p className="text-xs text-red-400">
                            {errors.shippingDetails.phoneNumber.message}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </section>
              ) : null}

              {step === 2 ? (
                <section className="space-y-5">
                  <h3 className="text-lg font-semibold">
                    Transparency Receipt
                  </h3>
                  <div className="rounded-lg border border-white/10 bg-black/30 p-4">
                    <div className="space-y-3 text-sm">
                      <div className="flex items-center justify-between text-zinc-300">
                        <span>1. CIF Price (Base vehicle price)</span>
                        <span>{formatLkr(cifPrice)}</span>
                      </div>
                      <div className="flex items-center justify-between text-zinc-300">
                        <span>2. Estimated Customs Duty (30% of CIF)</span>
                        <span>{formatLkr(estimatedCustomsDuty)}</span>
                      </div>
                      <div className="flex items-center justify-between text-zinc-300">
                        <span>3. Clearing & Port Charges</span>
                        <span>{formatLkr(CLEARING_AND_PORT_CHARGES)}</span>
                      </div>
                      <div className="flex items-center justify-between text-zinc-300">
                        <span>4. ClearDrive Service Fee</span>
                        <span>{formatLkr(CLEARDRIVE_SERVICE_FEE)}</span>
                      </div>
                      <Separator className="bg-white/10" />
                      <div className="flex items-center justify-between text-base font-semibold text-white">
                        <span>5. Total Landed Cost</span>
                        <span>{formatLkr(totalLandedCost)}</span>
                      </div>
                    </div>
                  </div>

                  <p className="flex items-center gap-2 text-xs text-zinc-400">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    Finalize this order to proceed to payment and live journey
                    tracking.
                  </p>
                </section>
              ) : null}
            </motion.div>
          </AnimatePresence>
        </CardContent>

        <CardFooter className="flex flex-col gap-4 border-t border-white/10 pt-6">
          {submitError ? (
            <p className="w-full text-sm text-red-400">{submitError}</p>
          ) : null}
          <div className="flex w-full justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={previousStep}
              disabled={step === 0 || isSubmitting}
              className="border-white/15 bg-transparent text-white hover:bg-white/10"
            >
              <ChevronLeft className="mr-2 h-4 w-4" />
              Back
            </Button>

            {step < STEP_TITLES.length - 1 ? (
              <Button
                type="button"
                onClick={nextStep}
                className="bg-[#FE7743] font-semibold text-black hover:bg-[#FE7743]/90"
              >
                Continue
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-[#FE7743] font-semibold text-black hover:bg-[#FE7743]/90"
              >
                {isSubmitting ? "Submitting..." : "Confirm & Place Order"}
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>
    </form>
  );
}
