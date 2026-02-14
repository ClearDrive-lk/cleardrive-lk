"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calculator, TrendingUp, AlertCircle } from "lucide-react";

interface CostCalculatorProps {
  priceJPY: number;
  engineCC: number;
  year: number;
}

export function CostCalculator({ priceJPY, engineCC }: CostCalculatorProps) {
  // Exchange Rate (Mock Live Data)
  const RATE_JPY_LKR = 2.25;
  const FREIGHT_USD = 1200;
  const RATE_USD_LKR = 310;

  // --- CALCULATION LOGIC (Done directly in render) ---

  // 1. CIF Value
  const carCostLKR = priceJPY * RATE_JPY_LKR;
  const freightLKR = FREIGHT_USD * RATE_USD_LKR;
  const insuranceLKR = carCostLKR * 0.01; // 1% est
  const calculatedCIF = carCostLKR + freightLKR + insuranceLKR;

  // 2. Taxes
  let dutyRate = 0;
  if (engineCC < 1000) dutyRate = 1.5; // 150%
  else if (engineCC < 1500) dutyRate = 2.2; // 220%
  else dutyRate = 3.0; // 300%

  const taxAmount = calculatedCIF * dutyRate;

  // 3. Totals
  const clearingFee = 45000;
  const portCharges = 25000;
  const totalLanded = calculatedCIF + taxAmount + clearingFee + portCharges;

  // Formatter
  const formatLKR = (amount: number) =>
    new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      maximumSignificantDigits: 3,
    }).format(amount);

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
            <span>Auction Price ({priceJPY.toLocaleString()} JPY)</span>
            <span>{(priceJPY * RATE_JPY_LKR).toLocaleString()} LKR</span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Freight & Insurance</span>
            <span>
              {(
                FREIGHT_USD * RATE_USD_LKR +
                priceJPY * RATE_JPY_LKR * 0.01
              ).toLocaleString()}{" "}
              LKR
            </span>
          </div>
          <div className="flex justify-between font-bold text-white pt-2 border-t border-white/5">
            <span>CIF Value (Colombo)</span>
            <span>
              {calculatedCIF.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}{" "}
              LKR
            </span>
          </div>
        </div>

        {/* Taxes */}
        <div className="p-3 bg-[#1A1A1A] rounded-lg space-y-2 border border-white/5">
          <div className="flex items-center gap-2 text-[#FE7743] text-xs mb-2">
            <AlertCircle className="w-3 h-3" />
            <span>Government Levies (Est.)</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>Excise Duty</span>
            <span>Incl.</span>
          </div>
          <div className="flex justify-between text-gray-400 text-xs">
            <span>PAL / VAT / CESS</span>
            <span>Incl.</span>
          </div>
          <div className="flex justify-between text-white font-bold pt-1 border-t border-white/5">
            <span>Total Taxes</span>
            <span>
              {taxAmount.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}{" "}
              LKR
            </span>
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
                <span>+12% vs last month</span>
              </div>
            </div>
            <div className="text-2xl font-bold text-[#FE7743]">
              {formatLKR(totalLanded)}
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
