"use client";

import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { Calculator } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import apiClient from "@/lib/api-client";
import { Vehicle } from "@/types/vehicle";

interface CostCalculatorProps {
  vehicleId: string;
  vehicle: Vehicle;
}

type BaseCostBreakdown = {
  exchange_rate: number | string;
  shipping_cost_lkr: number | string;
};

type TaxCalculationResponse = {
  cif_value: number;
  customs_duty: number;
  surcharge: number;
  excise_duty: number;
  cess: number;
  vat: number;
  pal: number;
  luxury_tax: number;
  vel: number;
  com_exm_sel: number;
  total_duty: number;
  total_payable_to_customs: number;
  total_landed_cost: number;
  effective_rate_percent: number;
  rule_used: Record<string, number | string | null>;
};

function formatLKR(amount: number) {
  return new Intl.NumberFormat("en-LK", {
    style: "currency",
    currency: "LKR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatJPY(amount: number) {
  return new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

function toNumber(value: number | string | undefined) {
  return value === undefined ? 0 : Number(value);
}

function resolveImportDate(value: string | Date | undefined) {
  const parsed = value ? new Date(value) : new Date();
  if (Number.isNaN(parsed.getTime())) {
    return new Date().toISOString().slice(0, 10);
  }
  return parsed.toISOString().slice(0, 10);
}

function deriveTaxInputs(vehicle: Vehicle) {
  const fuel = vehicle.fuel.trim().toLowerCase();
  const vehicleType = (vehicle.vehicleType || "OTHER").trim().toUpperCase();

  if (fuel.includes("electric")) {
    return {
      rawFuelType: "ELECTRIC",
      catalogFuelType: "Electric",
      vehicleType,
    };
  }

  if (fuel.includes("diesel") && fuel.includes("hybrid")) {
    return {
      rawFuelType: "HYBRID",
      catalogFuelType: "Diesel/hybrid",
      vehicleType,
    };
  }

  if (fuel.includes("hybrid")) {
    return {
      rawFuelType: "HYBRID",
      catalogFuelType: "Gasoline/hybrid",
      vehicleType,
    };
  }

  if (fuel.includes("diesel")) {
    return {
      rawFuelType: "DIESEL",
      catalogFuelType: "Diesel",
      vehicleType,
    };
  }

  return {
    rawFuelType: "PETROL",
    catalogFuelType: "Petrol",
    vehicleType,
  };
}

export function CostCalculator({ vehicleId, vehicle }: CostCalculatorProps) {
  const hasPrice = Number.isFinite(vehicle.priceJPY) && vehicle.priceJPY > 0;
  const taxInputs = deriveTaxInputs(vehicle);

  const {
    data: baseCost,
    isLoading: isBaseLoading,
    isError: isBaseError,
    error: baseError,
  } = useQuery<BaseCostBreakdown>({
    queryKey: ["vehicle-cost-base", vehicleId],
    queryFn: async () => {
      const response = await apiClient.get(`/vehicles/${vehicleId}/cost`);
      return response.data;
    },
    enabled: Boolean(vehicleId),
    staleTime: 1000 * 60 * 5,
  });

  const {
    data: result,
    isLoading: isTaxLoading,
    isError: isTaxError,
    error: taxError,
  } = useQuery<TaxCalculationResponse>({
    queryKey: [
      "vehicle-tax-estimate",
      vehicleId,
      vehicle.priceJPY,
      vehicle.engineCC,
      vehicle.fuel,
      vehicle.vehicleType,
      baseCost?.exchange_rate,
      baseCost?.shipping_cost_lkr,
    ],
    queryFn: async () => {
      const exchangeRate = toNumber(baseCost?.exchange_rate);
      const shippingCostLkr = toNumber(baseCost?.shipping_cost_lkr);
      const cifValueLkr = Math.round(
        vehicle.priceJPY * exchangeRate + shippingCostLkr,
      );

      const response = await apiClient.post<TaxCalculationResponse>(
        "/calculate/tax",
        {
          vehicle_type: taxInputs.vehicleType,
          fuel_type: taxInputs.rawFuelType,
          engine_cc: vehicle.engineCC ?? 0,
          power_kw: null,
          vehicle_age_years: 0,
          vehicle_condition: "BRAND_NEW",
          import_date: resolveImportDate(vehicle.endTime),
          catalog_vehicle_type: taxInputs.vehicleType,
          catalog_fuel_type: taxInputs.catalogFuelType,
          cif_value: cifValueLkr,
        },
      );
      return response.data;
    },
    enabled: Boolean(
      vehicleId &&
      hasPrice &&
      baseCost &&
      Number.isFinite(toNumber(baseCost.exchange_rate)) &&
      (vehicle.engineCC ?? 0) > 0,
    ),
    staleTime: 1000 * 60 * 5,
  });

  const isLoading = isBaseLoading || isTaxLoading;
  const error = taxError ?? baseError;
  const isError = isBaseError || isTaxError;

  if (isLoading) {
    return (
      <Card className="border-[#546a7b]/65 bg-[#fdfdff] sticky top-6">
        <CardHeader className="pb-2 border-b border-[#546a7b]/40">
          <div className="flex items-center justify-between">
            <CardTitle className="text-[#393d3f] flex items-center gap-2">
              <Calculator className="w-4 h-4 text-[#62929e]" />
              Landed Cost Analysis
            </CardTitle>
            <Badge
              variant="outline"
              className="border-[#546a7b]/65 bg-[#c6c5b9]/20 text-[#546a7b] text-[10px]"
            >
              Loading
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <div className="h-4 w-3/4 rounded bg-[#c6c5b9]/20 animate-pulse" />
          <div className="h-4 w-2/3 rounded bg-[#c6c5b9]/20 animate-pulse" />
          <div className="h-4 w-full rounded bg-[#c6c5b9]/20 animate-pulse" />
          <div className="h-16 w-full rounded bg-[#c6c5b9]/20 animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !result || !baseCost) {
    const apiDetail = isAxiosError(error)
      ? (
          error.response?.data as
            | { detail?: { message?: string } | string }
            | undefined
        )?.detail
      : undefined;
    const errorMessage =
      typeof apiDetail === "string"
        ? apiDetail
        : apiDetail?.message ||
          "Unable to load the tax breakdown right now. Try again in a moment.";

    return (
      <Card className="border-[#546a7b]/65 bg-[#fdfdff] sticky top-6">
        <CardHeader className="pb-2 border-b border-[#546a7b]/40">
          <div className="flex items-center justify-between">
            <CardTitle className="text-[#393d3f] flex items-center gap-2">
              <Calculator className="w-4 h-4 text-[#62929e]" />
              Landed Cost Analysis
            </CardTitle>
            <Badge
              variant="outline"
              className="border-red-500/40 bg-red-500/10 text-red-300 text-[10px]"
            >
              Unavailable
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-4 text-sm text-gray-400 space-y-2">
          <p>{errorMessage}</p>
        </CardContent>
      </Card>
    );
  }

  const exchangeRate = toNumber(baseCost.exchange_rate);
  const shippingCostLkr = toNumber(baseCost.shipping_cost_lkr);
  const vehiclePriceLkr = Math.round(vehicle.priceJPY * exchangeRate);
  const ruleUsed = result.rule_used ?? {};
  const luxuryThreshold = Number(ruleUsed.luxury_tax_threshold ?? 0);
  const luxuryTaxBase =
    luxuryThreshold > 0 ? Math.max(result.cif_value - luxuryThreshold, 0) : 0;
  const exciseRate = Number(ruleUsed.excise_rate ?? 0);
  const minimumFlatExcise = Number(ruleUsed.min_excise_flat_rate_lkr ?? 0);
  const calculatedCcExcise = Number(ruleUsed.calculated_cc_excise ?? 0);
  const capacityInput = Number(
    ruleUsed.capacity_input ?? vehicle.engineCC ?? 0,
  );
  const capacityUnit = String(ruleUsed.capacity_unit ?? "cc").toLowerCase();
  const exciseRateLabel =
    minimumFlatExcise > 0 && result.excise_duty === minimumFlatExcise
      ? `${formatNumber(exciseRate)}/${capacityUnit} floor ${formatLKR(minimumFlatExcise)}`
      : `${formatNumber(exciseRate)}/${capacityUnit}`;

  const taxRows = [
    {
      code: "CID",
      base: result.cif_value,
      rate: `${formatNumber(Number(ruleUsed.customs_percent ?? 0))}%`,
      amount: result.customs_duty,
    },
    {
      code: "SUR",
      base: result.customs_duty,
      rate: `${formatNumber(Number(ruleUsed.surcharge_percent ?? 0))}%`,
      amount: result.surcharge,
    },
    {
      code: "XID",
      base: capacityInput,
      rate: exciseRateLabel,
      amount: result.excise_duty,
      helper:
        minimumFlatExcise > 0 && calculatedCcExcise < minimumFlatExcise
          ? "Minimum flat rate applied"
          : undefined,
    },
    ...(result.luxury_tax > 0
      ? [
          {
            code: "LXT",
            base: luxuryTaxBase,
            rate: `${formatNumber(Number(ruleUsed.luxury_tax_percent ?? 0))}%`,
            amount: result.luxury_tax,
          },
        ]
      : []),
    {
      code: "VAT",
      base: Number(ruleUsed.vat_base ?? 0),
      rate: `${formatNumber(Number(ruleUsed.vat_percent ?? 0))}%`,
      amount: result.vat,
    },
    ...(result.pal > 0
      ? [
          {
            code: "PAL",
            base: result.cif_value,
            rate: `${formatNumber(Number(ruleUsed.pal_percent ?? 0))}%`,
            amount: result.pal,
          },
        ]
      : []),
    ...(result.cess > 0
      ? [
          {
            code: "CESS",
            base: result.cif_value,
            rate: `${formatNumber(Number(ruleUsed.cess_percent ?? 0))}%`,
            amount: result.cess,
          },
        ]
      : []),
    ...(result.vel > 0
      ? [
          {
            code: "VEL",
            base: 1,
            rate: `${formatLKR(result.vel)}/Unit`,
            amount: result.vel,
          },
        ]
      : []),
    ...(result.com_exm_sel > 0
      ? [
          {
            code: "COM/EXM/SEL",
            base: 1,
            rate: `${formatLKR(result.com_exm_sel)}/Unit`,
            amount: result.com_exm_sel,
          },
        ]
      : []),
  ];

  return (
    <Card className="border-[#546a7b]/65 bg-[#fdfdff] sticky top-6">
      <CardHeader className="pb-2 border-b border-[#546a7b]/40">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[#393d3f] flex items-center gap-2">
            <Calculator className="w-4 h-4 text-[#62929e]" />
            Landed Cost Analysis
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="border-[#62929e]/40 bg-[#62929e]/10 text-[#62929e] text-[10px]"
            >
              HS {String(ruleUsed.hs_code ?? "N/A")}
            </Badge>
            <Badge
              variant="outline"
              className="border-green-900 bg-green-900/10 text-green-500 text-[10px]"
            >
              LIVE RATE
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4 font-mono text-sm">
        <div className="space-y-2">
          <div className="flex justify-between text-[#546a7b]">
            <span>
              Auction Price ({hasPrice ? formatJPY(vehicle.priceJPY) : "N/A"})
            </span>
            <span>{formatLKR(vehiclePriceLkr)}</span>
          </div>
          <div className="flex justify-between text-[#546a7b]">
            <span>Shipping & Insurance</span>
            <span>{formatLKR(shippingCostLkr)}</span>
          </div>
          <div className="flex justify-between font-bold text-[#393d3f] pt-2 border-t border-[#546a7b]/40">
            <span>Exchange Rate</span>
            <span>1 JPY = {exchangeRate.toFixed(2)} LKR</span>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-[#546a7b]/40 p-3">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#546a7b]">
              CIF Value (LKR)
            </p>
            <p className="mt-1 text-base font-bold text-[#393d3f]">
              {formatLKR(result.cif_value)}
            </p>
          </div>
          <div className="rounded-lg border border-[#546a7b]/40 p-3">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#546a7b]">
              Total Tax
            </p>
            <p className="mt-1 text-base font-bold text-[#393d3f]">
              {formatLKR(result.total_duty)}
            </p>
          </div>
          <div className="rounded-lg border border-[#546a7b]/40 p-3">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#546a7b]">
              CIF + Taxes Total
            </p>
            <p className="mt-1 text-base font-bold text-[#62929e]">
              {formatLKR(result.total_landed_cost)}
            </p>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg border border-[#546a7b]/40">
          <Table>
            <TableHeader>
              <TableRow className="border-[#546a7b]/40">
                <TableHead>Type</TableHead>
                <TableHead>Tax Base</TableHead>
                <TableHead>Rate</TableHead>
                <TableHead className="text-right">Amount (LKR)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {taxRows.map((row) => (
                <TableRow key={row.code} className="border-[#546a7b]/30">
                  <TableCell className="font-medium">{row.code}</TableCell>
                  <TableCell>{formatNumber(row.base)}</TableCell>
                  <TableCell>{row.rate}</TableCell>
                  <TableCell className="text-right">
                    {formatLKR(row.amount)}
                  </TableCell>
                </TableRow>
              ))}
              <TableRow className="border-[#546a7b]/30">
                <TableCell className="font-semibold">Total Tax</TableCell>
                <TableCell />
                <TableCell />
                <TableCell className="text-right font-semibold">
                  {formatLKR(result.total_duty)}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <div className="text-[10px] text-[#393d3f] text-center pt-2">
          *Estimates only. Final duty based on Customs valuation on arrival
          date.
        </div>
      </CardContent>
    </Card>
  );
}
