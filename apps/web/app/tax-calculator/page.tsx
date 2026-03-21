"use client";

import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import Header from "@/components/layout/Header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import apiClient from "@/lib/api-client";
import { useExchangeRate } from "@/lib/hooks/useExchangeRate";
import {
  ArrowUpRight,
  Calculator,
  Download,
  ExternalLink,
  FileText,
  Phone,
  ReceiptText,
} from "lucide-react";

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

type FuelPreset = {
  value: string;
  label: string;
  rawFuelType: "PETROL" | "DIESEL" | "ELECTRIC" | "HYBRID";
  catalogFuelType: string;
};

type ReferenceDocument = {
  id: string;
  title: string;
  issued_label: string;
  file_url: string;
};

const fuelOptions: FuelPreset[] = [
  {
    value: "petrol",
    label: "Petrol",
    rawFuelType: "PETROL",
    catalogFuelType: "Petrol",
  },
  {
    value: "diesel",
    label: "Diesel",
    rawFuelType: "DIESEL",
    catalogFuelType: "Diesel",
  },
  {
    value: "electric",
    label: "Electric",
    rawFuelType: "ELECTRIC",
    catalogFuelType: "Electric",
  },
  {
    value: "petrol-hybrid",
    label: "Petrol Hybrid",
    rawFuelType: "HYBRID",
    catalogFuelType: "Gasoline/hybrid",
  },
  {
    value: "diesel-hybrid",
    label: "Diesel Hybrid",
    rawFuelType: "HYBRID",
    catalogFuelType: "Diesel/hybrid",
  },
  {
    value: "e-power-hybrid",
    label: "E-Power Hybrid",
    rawFuelType: "HYBRID",
    catalogFuelType: "E-Power Hybrid",
  },
];

const vehicleOptions = [
  { value: "SUV", label: "SUV" },
  { value: "SEDAN", label: "Sedan" },
  { value: "VAN", label: "Van" },
  { value: "TRUCK", label: "Truck" },
  { value: "OTHER", label: "Other" },
];

const CBSL_EXCHANGE_RATE_URL =
  "https://www.cbsl.gov.lk/cbsl_custom/exratestt/exratestt.php";

const defaultForm = {
  cifJpy: "",
  exchangeRate: "",
  vehicleType: "",
  fuelPreset: "",
  engineCc: "",
  powerKw: "",
  importDate: "2026-03-21",
};

function formatLkr(value: number) {
  return new Intl.NumberFormat("en-LK", {
    style: "currency",
    currency: "LKR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatJpy(value: number) {
  return new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

function AmountText({
  value,
  accent = false,
}: {
  value: string;
  accent?: boolean;
}) {
  return (
    <span
      className={`block max-w-full overflow-hidden text-ellipsis break-words leading-tight ${
        accent ? "text-[#FE7743]" : "text-white"
      }`}
    >
      {value}
    </span>
  );
}

export default function TaxCalculatorPage() {
  const { data: exchangeRateData } = useExchangeRate();
  const [form, setForm] = useState(defaultForm);
  const [result, setResult] = useState<TaxCalculationResponse | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateTouched, setRateTouched] = useState(false);
  const [referenceDocuments, setReferenceDocuments] = useState<
    ReferenceDocument[]
  >([]);
  const [selectedDoc, setSelectedDoc] = useState<ReferenceDocument | null>(
    null,
  );

  useEffect(() => {
    const liveRate = exchangeRateData?.rate;
    if (liveRate == null) return;
    if (rateTouched) return;
    setForm((current) => ({ ...current, exchangeRate: liveRate.toFixed(5) }));
  }, [exchangeRateData?.rate, rateTouched]);

  useEffect(() => {
    let cancelled = false;
    async function loadReferenceDocuments() {
      try {
        const response = await apiClient.get<ReferenceDocument[]>(
          "/tax-reference-documents",
        );
        if (cancelled) return;
        setReferenceDocuments(response.data);
        setSelectedDoc((current) => current ?? response.data[0] ?? null);
      } catch {
        if (!cancelled) {
          setReferenceDocuments([]);
          setSelectedDoc(null);
        }
      }
    }
    void loadReferenceDocuments();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedFuel = fuelOptions.find(
    (option) => option.value === form.fuelPreset,
  );
  const cifJpy = Number(form.cifJpy) || 0;
  const exchangeRate = Number(form.exchangeRate) || 0;
  const calculatedCifLkr = Math.round(cifJpy * exchangeRate);

  async function handleCalculate() {
    if (!form.vehicleType || !selectedFuel) {
      setError("Select a vehicle type and fuel type first.");
      setResult(null);
      return;
    }
    setIsCalculating(true);
    setError(null);
    try {
      const response = await apiClient.post<TaxCalculationResponse>(
        "/calculate/tax",
        {
          vehicle_type: form.vehicleType,
          fuel_type: selectedFuel.rawFuelType,
          engine_cc: Number(form.engineCc) || 0,
          power_kw: form.powerKw ? Number(form.powerKw) : null,
          vehicle_age_years: 0,
          vehicle_condition: "BRAND_NEW",
          import_date: form.importDate,
          catalog_vehicle_type: form.vehicleType,
          catalog_fuel_type: selectedFuel.catalogFuelType,
          cif_value: calculatedCifLkr,
        },
      );
      setResult(response.data);
    } catch (requestError: unknown) {
      if (isAxiosError(requestError)) {
        const detail = requestError.response?.data as
          | { detail?: { message?: string } | string }
          | undefined;
        if (typeof detail?.detail === "string") {
          setError(detail.detail);
        } else if (detail?.detail && typeof detail.detail === "object") {
          setError(
            detail.detail.message ?? "Unable to calculate tax right now.",
          );
        } else {
          setError("Unable to calculate tax right now.");
        }
      } else {
        setError("Unable to calculate tax right now.");
      }
      setResult(null);
    } finally {
      setIsCalculating(false);
    }
  }

  function handleReset() {
    setForm(defaultForm);
    setResult(null);
    setError(null);
    setRateTouched(false);
  }

  const ruleUsed = result?.rule_used ?? {};
  const luxuryThreshold = Number(ruleUsed.luxury_tax_threshold ?? 0);
  const luxuryTaxBase =
    result && luxuryThreshold > 0
      ? Math.max(result.cif_value - luxuryThreshold, 0)
      : 0;
  const exciseRate = Number(ruleUsed.excise_rate ?? 0);
  const minimumFlatExcise = Number(ruleUsed.min_excise_flat_rate_lkr ?? 0);
  const calculatedCcExcise = Number(ruleUsed.calculated_cc_excise ?? 0);
  const capacityInput = Number(ruleUsed.capacity_input ?? 0);
  const capacityUnit = String(ruleUsed.capacity_unit ?? "cc").toLowerCase();
  const exciseRateLabel =
    minimumFlatExcise > 0 && result && result.excise_duty === minimumFlatExcise
      ? `${formatNumber(exciseRate)}/${capacityUnit} floor ${formatLkr(minimumFlatExcise)}`
      : `${formatNumber(exciseRate)}/${capacityUnit}`;

  const taxRows = result
    ? [
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
                rate: `${formatLkr(result.vel)}/Unit`,
                amount: result.vel,
              },
            ]
          : []),
        ...(result.com_exm_sel > 0
          ? [
              {
                code: "COM/EXM/SEL",
                base: 1,
                rate: `${formatLkr(result.com_exm_sel)}/Unit`,
                amount: result.com_exm_sel,
              },
            ]
          : []),
      ]
    : [];

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      <Header />
      <main>
        <section className="relative overflow-hidden border-b border-white/10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(254,119,67,0.18),transparent_38%),linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:auto,36px_36px,36px_36px]" />
          <div className="relative mx-auto max-w-7xl px-6 py-16">
            <div className="max-w-3xl space-y-5">
              <Badge className="border border-[#FE7743]/20 bg-[#FE7743]/10 px-3 py-1 font-mono text-[#FE7743]">
                Public Estimator
              </Badge>
              <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
                Vehicle Tax Calculator
              </h1>
              <p className="max-w-2xl text-base text-slate-300 md:text-lg">
                Estimate Sri Lankan import levies for vehicles imported from
                Japan, show the resolved HS code, and keep the supporting
                customs references visible on the same page.
              </p>
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-7xl gap-8 px-6 py-10 lg:grid-cols-[1.02fr_1.18fr]">
          <Card className="border-white/10 bg-[#0d0d0d]">
            <CardHeader className="border-b border-white/10">
              <CardTitle className="flex items-center gap-2 text-white">
                <Calculator className="h-5 w-5 text-[#FE7743]" />
                For Vehicles Imported from Japan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5 pt-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="cifJpy">CIF Value (JPY)</Label>
                  <Input
                    id="cifJpy"
                    value={form.cifJpy}
                    onChange={(event) =>
                      setForm({ ...form, cifJpy: event.target.value })
                    }
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exchangeRate">JPY to LKR Rate</Label>
                  <Input
                    id="exchangeRate"
                    value={form.exchangeRate}
                    onChange={(event) => {
                      setRateTouched(true);
                      setForm({ ...form, exchangeRate: event.target.value });
                    }}
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
              </div>

              <a
                href={CBSL_EXCHANGE_RATE_URL}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 text-sm text-[#FE7743] hover:text-orange-200"
              >
                {exchangeRateData?.source ||
                  "View Sri Lanka Customs Weekly Exchange Rates"}
                <ArrowUpRight className="h-4 w-4" />
              </a>
              <p className="text-xs text-slate-500">
                Live rate{" "}
                {exchangeRateData?.date
                  ? `for ${new Date(exchangeRateData.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`
                  : "loading from the internet"}
                .
              </p>
              {exchangeRateData?.rate != null ? (
                <button
                  type="button"
                  onClick={() => {
                    const liveRate = exchangeRateData.rate;
                    if (liveRate == null) return;
                    setRateTouched(false);
                    setForm((current) => ({
                      ...current,
                      exchangeRate: liveRate.toFixed(5),
                    }));
                  }}
                  className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-white"
                >
                  Use live CBSL rate
                </button>
              ) : null}

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Vehicle Type</Label>
                  <Select
                    value={form.vehicleType}
                    onValueChange={(value) =>
                      setForm({ ...form, vehicleType: value })
                    }
                  >
                    <SelectTrigger className="border-white/15 bg-[#161616] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                      <SelectValue placeholder="Select vehicle type" />
                    </SelectTrigger>
                    <SelectContent className="border-white/15 bg-[#121212] text-white">
                      {vehicleOptions.map((option) => (
                        <SelectItem
                          key={option.value}
                          value={option.value}
                          className="text-white focus:bg-[#222] focus:text-white"
                        >
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Fuel Type</Label>
                  <Select
                    value={form.fuelPreset}
                    onValueChange={(value) =>
                      setForm({ ...form, fuelPreset: value })
                    }
                  >
                    <SelectTrigger className="border-white/15 bg-[#161616] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent className="border-white/15 bg-[#121212] text-white">
                      {fuelOptions.map((option) => (
                        <SelectItem
                          key={option.value}
                          value={option.value}
                          className="text-white focus:bg-[#222] focus:text-white"
                        >
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="engineCc">Engine Capacity (cc)</Label>
                  <Input
                    id="engineCc"
                    value={form.engineCc}
                    onChange={(event) =>
                      setForm({ ...form, engineCc: event.target.value })
                    }
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="importDate">Import Date</Label>
                  <Input
                    id="importDate"
                    type="date"
                    value={form.importDate}
                    onChange={(event) =>
                      setForm({ ...form, importDate: event.target.value })
                    }
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
              </div>

              {selectedFuel?.rawFuelType === "ELECTRIC" && (
                <div className="space-y-2">
                  <Label htmlFor="powerKw">Motor Power (kW)</Label>
                  <Input
                    id="powerKw"
                    value={form.powerKw}
                    onChange={(event) =>
                      setForm({ ...form, powerKw: event.target.value })
                    }
                    className="border-white/10 bg-white/5 text-white"
                  />
                </div>
              )}

              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleCalculate}
                  disabled={isCalculating}
                  className="bg-[#FE7743] text-black hover:bg-[#ff8b5e]"
                >
                  {isCalculating ? "Calculating..." : "Calculate Tax"}
                </Button>
                <Button
                  onClick={handleReset}
                  variant="outline"
                  className="border-white/15 bg-transparent text-white hover:bg-white/5"
                >
                  Reset
                </Button>
              </div>

              <p className="text-sm text-slate-400">
                Current input converts{" "}
                <span className="font-mono text-white">
                  {formatJpy(cifJpy)}
                </span>{" "}
                to{" "}
                <span className="font-mono text-white">
                  {formatLkr(calculatedCifLkr)}
                </span>
                .
              </p>

              {error ? <p className="text-sm text-red-300">{error}</p> : null}
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-[#0d0d0d]">
            <CardHeader className="border-b border-white/10">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="text-white">Tax Calculation</CardTitle>
                {result ? (
                  <Badge className="border border-emerald-500/30 bg-emerald-500/10 text-emerald-300">
                    HS Code: {String(ruleUsed.hs_code ?? "N/A")}
                  </Badge>
                ) : (
                  <Badge className="border border-white/10 bg-white/5 text-slate-400">
                    Ready for calculation
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              {result ? (
                <>
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-2xl border border-white/10 bg-[#141414] p-4">
                      <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
                        CIF Value (LKR)
                      </div>
                      <div className="mt-2 text-2xl font-semibold md:text-3xl">
                        <AmountText value={formatLkr(result.cif_value)} />
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-[#141414] p-4">
                      <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
                        Total Tax
                      </div>
                      <div className="mt-2 text-2xl font-semibold md:text-3xl">
                        <AmountText
                          value={formatLkr(result.total_payable_to_customs)}
                          accent
                        />
                      </div>
                    </div>
                    <div className="rounded-2xl border border-[#FE7743]/20 bg-[#18110d] p-4">
                      <div className="text-xs uppercase tracking-[0.2em] text-slate-500">
                        CIF + Taxes Total
                      </div>
                      <div className="mt-2 text-2xl font-semibold md:text-3xl">
                        <AmountText
                          value={formatLkr(
                            result.cif_value + result.total_payable_to_customs,
                          )}
                        />
                      </div>
                    </div>
                  </div>

                  <Table>
                    <TableHeader>
                      <TableRow className="border-white/10 hover:bg-transparent">
                        <TableHead>Type</TableHead>
                        <TableHead>Tax Base</TableHead>
                        <TableHead>Rate</TableHead>
                        <TableHead className="min-w-[140px] text-right">
                          Amount (LKR)
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {taxRows.map((row) => (
                        <TableRow
                          key={row.code}
                          className="border-white/10 hover:bg-white/5"
                        >
                          <TableCell className="font-semibold text-white">
                            {row.code}
                            {"helper" in row && row.helper ? (
                              <div className="mt-1 text-[11px] font-normal text-slate-500">
                                {row.helper}
                              </div>
                            ) : null}
                          </TableCell>
                          <TableCell className="max-w-[140px] whitespace-normal break-words text-slate-300">
                            {formatNumber(Number(row.base))}
                          </TableCell>
                          <TableCell className="max-w-[180px] whitespace-normal break-words text-slate-300">
                            {row.rate}
                          </TableCell>
                          <TableCell className="max-w-[180px] whitespace-normal break-words text-right font-medium text-white">
                            {formatLkr(row.amount)}
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="border-white/10 bg-[#141414] hover:bg-[#141414]">
                        <TableCell className="font-semibold text-white">
                          Total Tax
                        </TableCell>
                        <TableCell />
                        <TableCell />
                        <TableCell className="max-w-[180px] whitespace-normal break-words text-right text-xl font-semibold text-[#FE7743]">
                          {formatLkr(result.total_payable_to_customs)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-white/10 bg-[#101010] p-8 text-slate-400">
                  Run a calculation to see the resolved HS code, CIF in LKR, and
                  the full levy stack.
                </div>
              )}

              <div className="rounded-2xl border border-[#FE7743]/15 bg-[#16110e] p-5 text-sm leading-7 text-slate-300">
                <div className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#FE7743]">
                  Disclaimer
                </div>
                This calculator provides estimated values based on the active
                rules and supporting reference documents currently configured in
                ClearDrive. It is intended for informational purposes only and
                should not be treated as legal, financial, or customs-clearance
                advice. Final assessments remain subject to Sri Lanka Customs.
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="mx-auto max-w-7xl px-6 pb-10">
          <Card
            id="reference-documents"
            className="border-white/10 bg-[#0d0d0d]"
          >
            <CardHeader className="border-b border-white/10">
              <CardTitle className="flex items-center gap-2 text-white">
                <ReceiptText className="h-5 w-5 text-[#FE7743]" />
                Reference Documents
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 pt-6 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="space-y-3">
                {referenceDocuments.map((document) => {
                  const isActive = selectedDoc?.id === document.id;
                  return (
                    <div
                      key={document.id}
                      className={`rounded-2xl border p-4 transition ${isActive ? "border-[#FE7743]/40 bg-[#1a130f]" : "border-white/10 bg-[#131313]"}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <div className="text-sm font-semibold text-white">
                            {document.title}
                          </div>
                          <div className="mt-1 text-xs text-slate-500">
                            {document.issued_label}
                          </div>
                        </div>
                        <FileText className="h-4 w-4 shrink-0 text-[#FE7743]" />
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setSelectedDoc(document)}
                          className="border-white/10 bg-transparent text-white hover:bg-white/5"
                        >
                          View
                        </Button>
                        <Button
                          asChild
                          className="bg-[#FE7743] text-black hover:bg-[#ff8b5e]"
                        >
                          <a href={document.file_url} download>
                            <Download className="mr-2 h-4 w-4" />
                            Download
                          </a>
                        </Button>
                      </div>
                    </div>
                  );
                })}
                <p className="text-xs leading-6 text-slate-500">
                  Admins can now manage these documents from
                  `/admin/reference-docs`.
                </p>
                <div className="rounded-2xl border border-dashed border-white/10 bg-[#111] p-4 text-xs leading-6 text-slate-400">
                  Use the admin upload screen to add PDFs. The public calculator
                  reads the active document list from the backend automatically.
                </div>
              </div>

              <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#111]">
                <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                  <div>
                    <div className="text-sm font-semibold text-white">
                      {selectedDoc?.title ?? "No document selected"}
                    </div>
                    <div className="text-xs text-slate-500">
                      {selectedDoc?.issued_label ??
                        "Upload a document from the admin panel."}
                    </div>
                  </div>
                  <a
                    href={selectedDoc?.file_url ?? "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-[#FE7743] hover:text-orange-200"
                  >
                    Open in new tab
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
                {selectedDoc ? (
                  <iframe
                    title={selectedDoc.title}
                    src={selectedDoc.file_url}
                    className="h-[540px] w-full bg-white"
                  />
                ) : (
                  <div className="flex h-[540px] items-center justify-center px-6 text-sm text-slate-400">
                    No active reference documents uploaded yet.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="border-t border-white/10 bg-[#080808]">
          <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-10 md:flex-row md:items-start md:justify-between">
            <div>
              <div className="text-sm uppercase tracking-[0.24em] text-slate-500">
                Contact Us
              </div>
              <div className="mt-4 flex items-center gap-3 text-white">
                <Phone className="h-4 w-4 text-[#FE7743]" />
                <span>077 66 10 600</span>
              </div>
              <a
                href="https://wa.me/94776610600"
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-flex items-center gap-2 text-sm text-[#FE7743] hover:text-orange-200"
              >
                Chat with us on WhatsApp
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
            <div className="max-w-xl text-sm leading-7 text-slate-400">
              Powered by Passion, Built on Trust. Keep the calculator, the
              active HS rules, and the supporting customs documents in one place
              so users can see both the estimate and the source basis behind it.
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
