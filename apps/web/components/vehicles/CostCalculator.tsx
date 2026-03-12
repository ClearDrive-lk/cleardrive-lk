"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calculator, TrendingUp, AlertCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";

interface CostCalculatorProps {
  vehicleId: string;
  priceJPY: number;
}

type CostBreakdown = {
  vehicle_price_jpy: number | string;
  vehicle_price_lkr: number | string;
  exchange_rate: number | string;
  shipping_cost_lkr: number | string;
  customs_duty_lkr: number | string;
  excise_duty_lkr: number | string;
  pal_lkr: number | string;
  vat_lkr: number | string;
  cess_lkr: number | string;
  port_charges_lkr: number | string;
  clearance_fee_lkr: number | string;
  documentation_fee_lkr: number | string;
  total_cost_lkr: number | string;
  vehicle_percentage: number | string;
  taxes_percentage: number | string;
  fees_percentage: number | string;
};

export function CostCalculator({ vehicleId, priceJPY }: CostCalculatorProps) {
  const { data, isLoading, isError } = useQuery<CostBreakdown>({
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
      maximumSignificantDigits: 3,
    }).format(amount);
  const formatJPY = (amount: number) =>
    new Intl.NumberFormat("ja-JP", {
      style: "currency",
      currency: "JPY",
      maximumSignificantDigits: 3,
    }).format(amount);

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
          Unable to load the tax breakdown right now. Try again in a moment.
        </CardContent>
      </Card>
    );
  }

  const taxesTotal =
    toNumber(data.customs_duty_lkr) +
    toNumber(data.excise_duty_lkr) +
    toNumber(data.vat_lkr) +
    toNumber(data.cess_lkr) +
    toNumber(data.pal_lkr);
  const feesTotal =
    toNumber(data.shipping_cost_lkr) +
    toNumber(data.port_charges_lkr) +
    toNumber(data.clearance_fee_lkr) +
    toNumber(data.documentation_fee_lkr);

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
            <span>Auction Price ({formatJPY(priceJPY)})</span>
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
            <AlertCircle className="w-3 h-3" />
            <span>Government Levies (Est.)</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>Customs Duty</span>
            <span>{formatLKR(toNumber(data.customs_duty_lkr))}</span>
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
                  Taxes {Number(data.taxes_percentage).toFixed(1)}% · Fees{" "}
                  {Number(data.fees_percentage).toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="text-2xl font-bold text-[#FE7743]">
              {formatLKR(toNumber(data.total_cost_lkr))}
            </div>
          </div>
        </div>

        <div className="text-[10px] text-gray-600 text-center pt-2">
          *Estimates only. Final duty based on Customs valuation on arrival
          date.
        </div>
      </CardContent>
    </Card>
  );
}
