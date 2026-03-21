"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calculator, Info, TrendingUp } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import apiClient from "@/lib/api-client";

interface CostCalculatorProps {
  vehicleId: string;
  priceJPY: number;
}

type CostBreakdown = {
  vehicle_price_jpy: number | string;
  vehicle_price_lkr: number | string;
  exchange_rate: number | string;
  exchange_rate_source?: string;
  exchange_rate_date?: string;
  exchange_rate_provider?: string;
  hs_code?: number | string;
  shipping_cost_lkr: number | string;
  customs_duty_lkr: number | string;
  surcharge_lkr?: number | string;
  excise_duty_lkr: number | string;
  pal_lkr: number | string;
  vat_lkr: number | string;
  cess_lkr: number | string;
  luxury_tax_lkr?: number | string;
  vel_lkr?: number | string;
  com_exm_sel_lkr?: number | string;
  port_charges_lkr: number | string;
  clearance_fee_lkr: number | string;
  documentation_fee_lkr: number | string;
  platform_fee_lkr?: number | string;
  platform_fee_percentage?: number | string;
  platform_fee_tier?: string;
  platform_fee_description?: string;
  platform_fee?: {
    amount: number | string;
    tier: string;
    description: string;
    percentage_of_total: number | string;
  };
  total_cost_lkr: number | string;
  vehicle_percentage: number | string;
  taxes_percentage: number | string;
  fees_percentage: number | string;
};

export function CostCalculator({ vehicleId, priceJPY }: CostCalculatorProps) {
  const hasPrice = Number.isFinite(priceJPY) && priceJPY > 0;
  const { data, isLoading, isError, error } = useQuery<CostBreakdown>({
    queryKey: ["vehicle-cost", vehicleId],
    queryFn: async () => {
      const response = await apiClient.get(`/vehicles/${vehicleId}/cost`);
      return response.data;
    },
    enabled: Boolean(vehicleId),
    staleTime: 1000 * 60 * 5,
  });

  const toNumber = (value: number | string | undefined) =>
    value === undefined ? 0 : Number(value);
  const formatLKR = (amount: number) =>
    new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  const formatJPY = (amount: number) =>
    new Intl.NumberFormat("ja-JP", {
      style: "currency",
      currency: "JPY",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  const formatRateDate = (value?: string) => {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (isLoading) {
    return (
      <Card className="border-white/10 bg-[#0F0F0F] sticky top-6">
        <CardHeader className="pb-2 border-b border-white/5">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Calculator className="w-4 h-4 text-[#FE7743]" />
              Landed Cost Analysis
            </CardTitle>
            <Badge
              variant="outline"
              className="border-white/10 bg-white/5 text-gray-400 text-[10px]"
            >
              Loading
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <div className="h-4 w-3/4 rounded bg-white/5 animate-pulse" />
          <div className="h-4 w-2/3 rounded bg-white/5 animate-pulse" />
          <div className="h-4 w-full rounded bg-white/5 animate-pulse" />
          <div className="h-16 w-full rounded bg-white/5 animate-pulse" />
          <div className="h-10 w-full rounded bg-white/5 animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !data) {
    const errorMessage = isAxiosError(error)
      ? ((error.response?.data as { detail?: string } | undefined)?.detail ??
        "Unable to load the tax breakdown right now. Try again in a moment.")
      : "Unable to load the tax breakdown right now. Try again in a moment.";
    return (
      <Card className="border-white/10 bg-[#0F0F0F] sticky top-6">
        <CardHeader className="pb-2 border-b border-white/5">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Calculator className="w-4 h-4 text-[#FE7743]" />
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
        <CardContent className="pt-4 text-sm text-gray-400">
          {errorMessage}
        </CardContent>
      </Card>
    );
  }

  const taxesTotal =
    toNumber(data.customs_duty_lkr) +
    toNumber(data.surcharge_lkr) +
    toNumber(data.excise_duty_lkr) +
    toNumber(data.vat_lkr) +
    toNumber(data.cess_lkr) +
    toNumber(data.pal_lkr) +
    toNumber(data.luxury_tax_lkr) +
    toNumber(data.vel_lkr) +
    toNumber(data.com_exm_sel_lkr);
  const feesTotal =
    toNumber(data.shipping_cost_lkr) +
    toNumber(data.port_charges_lkr) +
    toNumber(data.clearance_fee_lkr) +
    toNumber(data.documentation_fee_lkr);
  const platformFeeAmount = toNumber(
    data.platform_fee?.amount ?? data.platform_fee_lkr,
  );
  const platformFeePercentage = toNumber(
    data.platform_fee?.percentage_of_total ?? data.platform_fee_percentage,
  );

  return (
    <Card className="border-white/10 bg-[#0F0F0F] sticky top-6">
      <CardHeader className="pb-2 border-b border-white/5">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Calculator className="w-4 h-4 text-[#FE7743]" />
            Landed Cost Analysis
          </CardTitle>
          <Badge
            variant="outline"
            className="border-green-900 bg-green-900/10 text-green-500 text-[10px]"
          >
            LIVE RATE
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4 font-mono text-sm">
        {/* Base Cost */}
        <div className="space-y-2">
          <div className="flex justify-between text-gray-400">
            <span>HS Code</span>
            <span>{String(data.hs_code || "N/A")}</span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>
              Auction Price ({hasPrice ? formatJPY(priceJPY) : "N/A"})
            </span>
            <span>{formatLKR(toNumber(data.vehicle_price_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Shipping & Insurance</span>
            <span>{formatLKR(toNumber(data.shipping_cost_lkr))}</span>
          </div>
          <div className="flex justify-between font-bold text-white pt-2 border-t border-white/5">
            <span>Exchange Rate</span>
            <span>1 JPY = {Number(data.exchange_rate).toFixed(2)} LKR</span>
          </div>
        </div>

        {/* Taxes */}
        <div className="p-3 bg-[#1A1A1A] rounded-lg space-y-2 border border-white/5">
          <div className="flex items-center gap-2 text-[#FE7743] text-xs mb-2">
            <span>Government Levies (Est.)</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>Customs Duty</span>
            <span>{formatLKR(toNumber(data.customs_duty_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>Surcharge</span>
            <span>{formatLKR(toNumber(data.surcharge_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>Excise Duty</span>
            <span>{formatLKR(toNumber(data.excise_duty_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>VAT</span>
            <span>{formatLKR(toNumber(data.vat_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>PAL</span>
            <span>{formatLKR(toNumber(data.pal_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>CESS</span>
            <span>{formatLKR(toNumber(data.cess_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>Luxury Tax</span>
            <span>{formatLKR(toNumber(data.luxury_tax_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>VEL</span>
            <span>{formatLKR(toNumber(data.vel_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>COM_EXM_SEL</span>
            <span>{formatLKR(toNumber(data.com_exm_sel_lkr))}</span>
          </div>
          <div className="flex justify-between text-white font-bold pt-1 border-t border-white/5">
            <span>Total Taxes</span>
            <span>{formatLKR(taxesTotal)}</span>
          </div>
        </div>

        {/* Fees */}
        <div className="p-3 bg-[#141414] rounded-lg space-y-2 border border-white/5 text-xs">
          <div className="flex justify-between text-gray-400">
            <span>Port Charges</span>
            <span>{formatLKR(toNumber(data.port_charges_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Clearance Fee</span>
            <span>{formatLKR(toNumber(data.clearance_fee_lkr))}</span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Documentation Fee</span>
            <span>{formatLKR(toNumber(data.documentation_fee_lkr))}</span>
          </div>
          <div className="flex justify-between text-white font-bold pt-1 border-t border-white/5">
            <span>Total Fees</span>
            <span>{formatLKR(feesTotal)}</span>
          </div>
        </div>

        <div className="p-3 bg-[#17130e] rounded-lg space-y-2 border border-[#FE7743]/10 text-xs">
          <div className="flex justify-between items-start gap-3 text-gray-300">
            <div>
              <div className="text-white">ClearDrive Service Fee</div>
              <div className="mt-1 text-[11px] text-gray-500">
                Based on vehicle value range
              </div>
            </div>
            <span className="font-semibold text-[#FE7743]">
              {formatLKR(platformFeeAmount)}
            </span>
          </div>
          <details className="group rounded-md border border-white/5 bg-black/10 p-2 text-[11px] text-gray-400">
            <summary className="flex cursor-pointer list-none items-center gap-2 text-gray-300">
              <Info className="h-3.5 w-3.5 text-[#FE7743]" />
              How is this calculated?
            </summary>
            <div className="mt-2 space-y-1 pl-5">
              <div>{`< 8M -> 120K`}</div>
              <div>{`8M - 20M -> 180K`}</div>
              <div>{`> 20M -> 300K`}</div>
            </div>
          </details>
          <div className="flex justify-between text-gray-400">
            <span>Impact on Total</span>
            <span>{platformFeePercentage.toFixed(1)}%</span>
          </div>
        </div>

        {/* Final Total */}
        <div className="pt-4">
          <div className="flex justify-between items-end">
            <div className="space-y-1">
              <span className="text-gray-400 text-xs">
                Estimated On-the-Road Price
              </span>
              <div className="flex items-center gap-1 text-xs text-green-500">
                <TrendingUp className="w-3 h-3" />
                <span>
                  Taxes {Number(data.taxes_percentage).toFixed(1)}% - Fees{" "}
                  {Number(data.fees_percentage).toFixed(1)}% - Platform{" "}
                  {platformFeePercentage.toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="text-2xl font-bold text-[#FE7743]">
              {formatLKR(toNumber(data.total_cost_lkr))}
            </div>
          </div>
        </div>

        <div className="text-[10px] text-gray-600 text-center pt-2">
          {data.exchange_rate_source ? (
            <div>
              Source: {data.exchange_rate_source}
              {data.exchange_rate_date
                ? ` | Rate Date: ${formatRateDate(data.exchange_rate_date)}`
                : ""}
            </div>
          ) : null}
          *Estimates only. Final duty based on Customs valuation on arrival
          date.
        </div>
      </CardContent>
    </Card>
  );
}
