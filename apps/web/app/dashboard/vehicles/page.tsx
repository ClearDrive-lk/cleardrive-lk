"use client";

import { useState, Suspense, useEffect, useCallback } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Terminal,
  ChevronLeft,
  ChevronRight,
  Search,
  X,
  SlidersHorizontal,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetFooter,
} from "@/components/ui/sheet";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

import { useLogout } from "@/lib/hooks/useLogout";
import { useVehicles } from "@/lib/hooks/useVehicles";
import { useDebounce } from "@/lib/hooks/useDebounce";
import { VehicleCard } from "@/components/vehicles/VehicleCard";
import { VehicleGridSkeleton } from "@/components/vehicles/VehicleCardSkeleton";
import { useExchangeRate } from "@/lib/hooks/useExchangeRate";
import { useAppSelector } from "@/lib/store/store";
import { getAccessToken, getRefreshToken } from "@/lib/auth";

// --- CONSTANTS ---

function VehicleCatalog() {
  const { logout, isLoading: isLogoutLoading } = useLogout();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const hasSession = Boolean(getAccessToken() || getRefreshToken());
  const router = useRouter();
  const searchParams = useSearchParams();

  // -- URL STATE --
  const currentPage = Number(searchParams.get("page")) || 1;
  const currentSearch = searchParams.get("search") || "";
  const currentFuel = searchParams.get("fuel") || "All";
  const currentStatus = searchParams.get("status") || "All";
  const currentSort = searchParams.get("sort") || "year_desc";
  const currentType = searchParams.get("type") || "All";
  const currentCurrency =
    (searchParams.get("currency") as "LKR" | "JPY" | null) || "LKR";

  const { data: exchangeRateData } = useExchangeRate();
  const exchangeRate = exchangeRateData?.rate || 2.25;

  // Advanced Filters URL State
  const priceMaxLimit =
    currentCurrency === "LKR"
      ? 50000000
      : Math.max(1000000, Math.round(50000000 / exchangeRate));
  const currentMinPrice = Number(searchParams.get("minPrice")) || 0;
  const currentMaxPrice = Number(searchParams.get("maxPrice")) || priceMaxLimit;
  const currentMinYear = Number(searchParams.get("minYear")) || 2000;
  const currentMaxYear =
    Number(searchParams.get("maxYear")) || new Date().getFullYear();
  const currentMaxMileage = Number(searchParams.get("maxMileage")) || 200000;
  const currentTransmission = searchParams.get("transmission") || "All";
  const hasTypeParam = searchParams.has("type");
  const hasMinYearParam = searchParams.has("minYear");
  const hasMaxYearParam = searchParams.has("maxYear");
  const hasMaxMileageParam = searchParams.has("maxMileage");
  const hasTransmissionParam = searchParams.has("transmission");
  const hasAdvancedFilters =
    hasMinYearParam ||
    hasMaxYearParam ||
    hasMaxMileageParam ||
    hasTransmissionParam;

  // -- LOCAL STATE --
  const [searchTerm, setSearchTerm] = useState(currentSearch);
  const debouncedSearch = useDebounce(searchTerm, 500);

  // Sheet Local State (for applying only on "Apply")
  const [sheetOpen, setSheetOpen] = useState(false);
  const [priceRange, setPriceRange] = useState([
    currentMinPrice,
    currentMaxPrice,
  ]);
  const [yearRange, setYearRange] = useState([currentMinYear, currentMaxYear]);
  const [mileageLimit, setMileageLimit] = useState([currentMaxMileage]);
  const [selectedTransmission, setSelectedTransmission] =
    useState(currentTransmission);

  const handleSheetOpenChange = useCallback(
    (open: boolean) => {
      if (open) {
        setPriceRange([currentMinPrice, currentMaxPrice]);
        setYearRange([currentMinYear, currentMaxYear]);
        setMileageLimit([currentMaxMileage]);
        setSelectedTransmission(currentTransmission);
      }
      setSheetOpen(open);
    },
    [
      currentMinPrice,
      currentMaxPrice,
      currentMinYear,
      currentMaxYear,
      currentMaxMileage,
      currentTransmission,
    ],
  );

  const lkrToCurrent = (value: number) =>
    currentCurrency === "LKR" ? value : Math.round(value / exchangeRate);

  const quickFilters = [
    { label: "Toyota", params: { search: "Toyota" } },
    { label: "Honda", params: { search: "Honda" } },
    { label: "Under 5M", params: { maxPrice: lkrToCurrent(5000000) } },
    { label: "Gasoline/Hybrid", params: { fuel: "Gasoline/Hybrid" } },
    { label: "SUVs", params: { type: "SUV" } },
    { label: "Electric", params: { fuel: "Electric" } },
    { label: "Luxury > 15M", params: { minPrice: lkrToCurrent(15000000) } },
  ];

  // -- HANDLERS --
  const updateFilters = useCallback(
    (newParams: Record<string, string | number | undefined>) => {
      const baseParams: Record<string, string | number | undefined> = {
        page: currentPage,
        search: currentSearch || undefined,
        fuel: currentFuel,
        status: currentStatus,
        sort: currentSort,
        currency: currentCurrency,
        minPrice: currentMinPrice > 0 ? currentMinPrice : undefined,
        maxPrice: currentMaxPrice !== 50000000 ? currentMaxPrice : undefined,
        minYear: hasMinYearParam ? currentMinYear : undefined,
        maxYear: hasMaxYearParam ? currentMaxYear : undefined,
        maxMileage: hasMaxMileageParam ? currentMaxMileage : undefined,
        transmission: hasTransmissionParam ? currentTransmission : undefined,
        type: hasTypeParam ? currentType : undefined,
      };

      const mergedParams = { ...baseParams, ...newParams };

      if (!newParams.page) {
        mergedParams.page = 1;
      }

      const params = new URLSearchParams();
      Object.entries(mergedParams).forEach(([key, value]) => {
        if (value !== undefined && value !== "" && value !== "All") {
          params.set(key, String(value));
        }
      });

      const query = params.toString();
      router.push(`/dashboard/vehicles${query ? `?${query}` : ""}`);
    },
    [
      router,
      currentPage,
      currentSearch,
      currentFuel,
      currentStatus,
      currentSort,
      currentMinPrice,
      currentMaxPrice,
      currentMinYear,
      currentMaxYear,
      currentMaxMileage,
      currentTransmission,
      hasMinYearParam,
      hasMaxYearParam,
      hasMaxMileageParam,
      hasTransmissionParam,
      hasTypeParam,
      currentType,
      currentCurrency,
    ],
  );

  // -- SYNC DEBOUNCE WITH URL --
  useEffect(() => {
    if (debouncedSearch !== currentSearch) {
      void updateFilters({ search: debouncedSearch });
    }
  }, [debouncedSearch, currentSearch, updateFilters]);

  // -- DATA FETCHING --
  const { data, isLoading, isError, error, refetch } = useVehicles({
    page: currentPage,
    limit: 8,
    search: currentSearch,
    fuel: currentFuel === "All" ? undefined : currentFuel,
    status: currentStatus === "All" ? undefined : currentStatus,
    sort: currentSort,
    minPrice: currentMinPrice,
    maxPrice: currentMaxPrice === 50000000 ? undefined : currentMaxPrice,
    minYear: hasMinYearParam ? currentMinYear : undefined,
    maxYear: hasMaxYearParam ? currentMaxYear : undefined,
    maxMileage: hasMaxMileageParam ? currentMaxMileage : undefined,
    transmission: hasTransmissionParam ? currentTransmission : undefined,
    vehicleType: currentType === "All" ? undefined : currentType,
    priceCurrency: currentCurrency,
    exchangeRate,
  });

  const vehicles = data?.data || [];
  const totalItems = data?.total || 0;
  const totalPages = Math.ceil(totalItems / 8);

  useEffect(() => {
    const allowed = new Set([
      "page",
      "search",
      "fuel",
      "status",
      "sort",
      "currency",
      "minPrice",
      "maxPrice",
      "minYear",
      "maxYear",
      "maxMileage",
      "transmission",
      "type",
    ]);
    const params = new URLSearchParams(searchParams.toString());
    let changed = false;
    Array.from(params.keys()).forEach((key) => {
      if (!allowed.has(key)) {
        params.delete(key);
        changed = true;
      }
    });
    if (changed) {
      const query = params.toString();
      router.replace(`/dashboard/vehicles${query ? `?${query}` : ""}`);
    }
  }, [searchParams, router]);

  const applyAdvancedFilters = () => {
    updateFilters({
      minPrice: priceRange[0],
      maxPrice: priceRange[1],
      minYear: yearRange[0],
      maxYear: yearRange[1],
      maxMileage: mileageLimit[0],
      transmission: selectedTransmission,
    });
    setSheetOpen(false);
  };

  const clearFilters = () => {
    setSearchTerm("");
    router.push(`/dashboard/vehicles?currency=${currentCurrency}`);
  };

  const formatCompact = (val: number) => {
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `${(val / 1000).toFixed(0)}k`;
    return val.toString();
  };

  const handleCurrencyToggle = (next: "LKR" | "JPY") => {
    if (next === currentCurrency) return;
    const convert = (value: number | undefined) => {
      if (!value || value <= 0) return undefined;
      return next === "JPY"
        ? Math.round(value / exchangeRate)
        : Math.round(value * exchangeRate);
    };
    updateFilters({
      currency: next,
      minPrice: convert(currentMinPrice),
      maxPrice: convert(currentMaxPrice),
    });
  };

  return (
    <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
      {/* Grid Background */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none z-0" />

      {/* Navigation */}
      <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link
            href={isAuthenticated || hasSession ? "/dashboard" : "/"}
            className="font-bold text-xl tracking-tighter flex items-center gap-2"
          >
            <Terminal className="w-5 h-5 text-[#62929e]" />
            ClearDrive<span className="text-[#62929e]">.lk</span>
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
              className="hover:text-[#393d3f] transition-colors"
            >
              Orders
            </Link>
            <Link
              href="/dashboard/vehicles"
              className="text-[#393d3f] flex items-center gap-2"
            >
              Vehicles{" "}
              <Badge
                variant="outline"
                className="text-[10px] border-[#62929e]/20 text-[#62929e]"
              >
                LIVE
              </Badge>
            </Link>
            <Link
              href="/dashboard/kyc"
              className="hover:text-[#393d3f] transition-colors"
            >
              KYC
            </Link>
            <Link
              href="/dashboard/profile"
              className="hover:text-[#393d3f] transition-colors"
            >
              Profile
            </Link>
          </div>
          {isAuthenticated ? (
            <Button
              onClick={logout}
              disabled={isLogoutLoading}
              className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold h-9"
            >
              {isLogoutLoading ? "..." : "Sign Out"}
            </Button>
          ) : (
            <div className="flex gap-3">
              <Link href="/login">
                <Button
                  variant="ghost"
                  className="text-[#546a7b] hover:text-[#393d3f] hover:bg-[#c6c5b9]/20 font-mono h-9"
                >
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold h-9">
                  Get Access
                </Button>
              </Link>
            </div>
          )}
        </div>
      </nav>

      {/* Page Header */}
      <header className="relative z-10 pt-12 pb-8 px-6 border-b border-[#546a7b]/40">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-[#393d3f] mb-2 tracking-tight">
                Vehicle <span className="text-[#62929e]">Catalog</span>
              </h1>
              <p className="text-[#546a7b] max-w-2xl">
                Browse live auctions from USS Tokyo, JAA, and CAI.
              </p>
            </div>

            {(currentSearch ||
              currentFuel !== "All" ||
              currentStatus !== "All" ||
              currentType !== "All" ||
              currentMinPrice > 0 ||
              hasAdvancedFilters) && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                className="border-red-500/20 text-red-500 hover:bg-red-500/10 hover:text-red-400"
              >
                <X className="w-4 h-4 mr-2" /> Reset Filters
              </Button>
            )}
          </div>

          {/* Filter Bar */}
          <div className="flex flex-col gap-4">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#546a7b]" />
                <Input
                  placeholder="Search make, model, chassis..."
                  className="pl-10 h-10 bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] focus:border-[#62929e] hover:bg-[#c6c5b9]/30 transition-colors"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {/* Dropdowns & Sheet Trigger */}
              <div className="flex flex-wrap gap-2">
                <div className="flex items-center gap-1 rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-2 py-1">
                  <button
                    type="button"
                    onClick={() => handleCurrencyToggle("LKR")}
                    className={`px-2 py-1 text-xs rounded-full transition ${
                      currentCurrency === "LKR"
                        ? "bg-[#62929e] text-[#fdfdff]"
                        : "text-[#546a7b] hover:text-[#393d3f]"
                    }`}
                  >
                    LKR
                  </button>
                  <button
                    type="button"
                    onClick={() => handleCurrencyToggle("JPY")}
                    className={`px-2 py-1 text-xs rounded-full transition ${
                      currentCurrency === "JPY"
                        ? "bg-[#62929e] text-[#fdfdff]"
                        : "text-[#546a7b] hover:text-[#393d3f]"
                    }`}
                  >
                    JPY
                  </button>
                </div>

                <Select
                  value={currentType}
                  onValueChange={(val) => updateFilters({ type: val })}
                >
                  <SelectTrigger className="w-[140px] h-10 bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f]">
                    <SelectItem value="All">All Types</SelectItem>
                    <SelectItem value="SUV">SUV</SelectItem>
                    <SelectItem value="Sedan">Sedan</SelectItem>
                    <SelectItem value="Hatchback">Hatchback</SelectItem>
                    <SelectItem value="Van/minivan">Van/Minivan</SelectItem>
                    <SelectItem value="Wagon">Wagon</SelectItem>
                    <SelectItem value="Pickup">Pickup</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentFuel}
                  onValueChange={(val) => updateFilters({ fuel: val })}
                >
                  <SelectTrigger className="w-[120px] h-10 bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30">
                    <SelectValue placeholder="Fuel" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f]">
                    <SelectItem value="All">All Fuels</SelectItem>
                    <SelectItem value="Gasoline">Gasoline</SelectItem>
                    <SelectItem value="Gasoline/Hybrid">
                      Gasoline/Hybrid
                    </SelectItem>
                    <SelectItem value="Diesel">Diesel</SelectItem>
                    <SelectItem value="Electric">Electric</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentStatus}
                  onValueChange={(val) => updateFilters({ status: val })}
                >
                  <SelectTrigger className="w-[120px] h-10 bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f]">
                    <SelectItem value="All">All Status</SelectItem>
                    <SelectItem value="Available">Available</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentSort}
                  onValueChange={(val) => updateFilters({ sort: val })}
                >
                  <SelectTrigger className="w-[160px] h-10 bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30">
                    <SelectValue placeholder="Sort By" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f]">
                    <SelectItem value="newest">Newest Listed</SelectItem>
                    <SelectItem value="price_asc">
                      Price: Low to High
                    </SelectItem>
                    <SelectItem value="price_desc">
                      Price: High to Low
                    </SelectItem>
                    <SelectItem value="year_desc">Year: Newest</SelectItem>
                    <SelectItem value="mileage_asc">Mileage: Low</SelectItem>
                  </SelectContent>
                </Select>

                {/* Advanced Filter Sheet */}
                <Sheet open={sheetOpen} onOpenChange={handleSheetOpenChange}>
                  <SheetTrigger asChild>
                    <Button
                      variant="outline"
                      className="h-10 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30 hover:text-[#62929e]"
                    >
                      <SlidersHorizontal className="w-4 h-4 mr-2" /> Filters
                    </Button>
                  </SheetTrigger>
                  <SheetContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f] overflow-y-auto">
                    <SheetHeader className="mb-6">
                      <SheetTitle className="text-[#393d3f]">
                        Advanced Filters
                      </SheetTitle>
                      <SheetDescription className="text-[#546a7b]">
                        Refine your search with detail.
                      </SheetDescription>
                    </SheetHeader>

                    <div className="space-y-8">
                      {/* Price Range */}
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <Label className="text-sm font-medium">
                            Price Range ({currentCurrency})
                          </Label>
                          <span className="text-xs text-[#62929e] font-mono">
                            {formatCompact(priceRange[0])} -{" "}
                            {formatCompact(priceRange[1])}
                          </span>
                        </div>
                        <Slider
                          min={0}
                          max={priceMaxLimit}
                          step={currentCurrency === "LKR" ? 1000000 : 100000}
                          value={priceRange}
                          onValueChange={setPriceRange}
                          className="py-4"
                        />
                        <div className="text-[10px] text-[#546a7b]">
                          1 JPY = {exchangeRate.toFixed(2)} LKR
                          {exchangeRateData?.date
                            ? ` · ${exchangeRateData.date}`
                            : ""}
                        </div>
                      </div>

                      <Separator className="bg-[#c6c5b9]/30" />

                      {/* Year Range */}
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <Label className="text-sm font-medium">Year</Label>
                          <span className="text-xs text-[#62929e] font-mono">
                            {yearRange[0]} - {yearRange[1]}
                          </span>
                        </div>
                        <Slider
                          min={2000}
                          max={new Date().getFullYear()}
                          step={1}
                          value={yearRange}
                          onValueChange={setYearRange}
                          className="py-4"
                        />
                      </div>

                      <Separator className="bg-[#c6c5b9]/30" />

                      {/* Mileage */}
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <Label className="text-sm font-medium">
                            Max Mileage
                          </Label>
                          <span className="text-xs text-[#62929e] font-mono">
                            {mileageLimit[0].toLocaleString()} km
                          </span>
                        </div>
                        <Slider
                          min={0}
                          max={200000}
                          step={5000}
                          value={mileageLimit}
                          onValueChange={setMileageLimit}
                          className="py-4"
                        />
                      </div>

                      <Separator className="bg-[#c6c5b9]/30" />

                      {/* Transmission */}
                      <div className="space-y-4">
                        <Label className="text-sm font-medium">
                          Transmission
                        </Label>
                        <RadioGroup
                          value={selectedTransmission}
                          onValueChange={setSelectedTransmission}
                          className="flex flex-col space-y-2"
                        >
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem
                              value="All"
                              id="t-all"
                              className="border-[#546a7b]/65 text-[#62929e]"
                            />
                            <Label htmlFor="t-all" className="text-[#546a7b]">
                              Any
                            </Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem
                              value="Automatic"
                              id="t-at"
                              className="border-[#546a7b]/65 text-[#62929e]"
                            />
                            <Label htmlFor="t-at" className="text-[#546a7b]">
                              Automatic
                            </Label>
                          </div>
                        </RadioGroup>
                      </div>
                    </div>

                    <SheetFooter className="mt-8">
                      <Button
                        onClick={applyAdvancedFilters}
                        className="w-full bg-[#62929e] hover:bg-[#62929e]/90 text-[#fdfdff] font-bold"
                      >
                        Apply Filters
                      </Button>
                    </SheetFooter>
                  </SheetContent>
                </Sheet>
              </div>
            </div>

            {/* Quick Filter Chips */}
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
              {quickFilters.map((filter, index) => (
                <button
                  key={index}
                  onClick={() => updateFilters(filter.params)}
                  className="flex-shrink-0 px-3 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/40 hover:bg-[#c6c5b9]/30 hover:border-[#62929e]/50 text-xs font-medium text-[#546a7b] transition-all whitespace-nowrap"
                >
                  {filter.label}
                </button>
              ))}
            </div>

            {(currentSearch ||
              currentFuel !== "All" ||
              currentStatus !== "All" ||
              currentType !== "All" ||
              currentMinPrice > 0 ||
              hasAdvancedFilters) && (
              <div className="flex flex-wrap gap-2 pt-1 text-xs">
                {currentSearch && (
                  <button
                    onClick={() => updateFilters({ search: "" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f]"
                  >
                    Search: {currentSearch} ✕
                  </button>
                )}
                {currentFuel !== "All" && (
                  <button
                    onClick={() => updateFilters({ fuel: "All" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f]"
                  >
                    Fuel: {currentFuel} ✕
                  </button>
                )}
                {currentStatus !== "All" && (
                  <button
                    onClick={() => updateFilters({ status: "All" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f]"
                  >
                    Status: {currentStatus} ✕
                  </button>
                )}
                {currentType !== "All" && (
                  <button
                    onClick={() => updateFilters({ type: "All" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f]"
                  >
                    Type: {currentType} ✕
                  </button>
                )}
                {currentMinPrice > 0 && (
                  <button
                    onClick={() => updateFilters({ minPrice: undefined })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f]"
                  >
                    Min Price ✕
                  </button>
                )}
                {hasAdvancedFilters && (
                  <button
                    onClick={() =>
                      updateFilters({
                        minYear: undefined,
                        maxYear: undefined,
                        maxMileage: undefined,
                        transmission: "All",
                      })
                    }
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f]"
                  >
                    Advanced Filters ✕
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative z-10 px-6 py-8">
        <div className="max-w-7xl mx-auto">
          {isError ? (
            <div className="mb-8 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-center space-y-2">
              <div>Failed to load vehicles. Please try again later.</div>
              <div className="text-xs text-red-300/80">
                {(() => {
                  const err = error as {
                    message?: string;
                    response?: { status?: number; data?: unknown };
                  };
                  if (err?.response?.status) {
                    return `Status: ${err.response.status}`;
                  }
                  return err?.message || "Unknown error";
                })()}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void refetch()}
                className="border-red-500/30 text-red-200 hover:bg-red-500/10"
              >
                Retry
              </Button>
            </div>
          ) : isLoading ? (
            <VehicleGridSkeleton />
          ) : vehicles.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {vehicles.map((vehicle) => (
                  <VehicleCard key={vehicle.id} vehicle={vehicle} />
                ))}
              </div>

              {/* Pagination Controls */}
              <div className="mt-12 flex flex-col sm:flex-row justify-between items-center gap-4 border-t border-[#546a7b]/40 pt-8">
                <span className="text-sm text-[#546a7b]">
                  Showing {(currentPage - 1) * 8 + 1} to{" "}
                  {Math.min(currentPage * 8, totalItems)} of {totalItems}{" "}
                  entries
                </span>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage === 1}
                    onClick={() => updateFilters({ page: currentPage - 1 })}
                    className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20 disabled:opacity-30"
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" /> Prev
                  </Button>

                  <div className="px-4 py-1.5 rounded bg-[#c6c5b9]/20 text-sm font-mono text-[#546a7b]">
                    Page {currentPage} of {totalPages || 1}
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage >= totalPages}
                    onClick={() => updateFilters({ page: currentPage + 1 })}
                    className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20 disabled:opacity-30"
                  >
                    Next <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 bg-[#62929e]/10 rounded-full flex items-center justify-center mb-6">
                <Search className="w-8 h-8 text-[#62929e]" />
              </div>
              <h3 className="text-2xl font-bold text-[#393d3f] mb-2">
                No Vehicles Found
              </h3>
              <p className="text-[#546a7b] max-w-md mx-auto mb-8">
                We couldn&apos;t find any vehicles matching your search
                criteria. Try adjusting your filters or search term.
              </p>
              <div className="flex flex-wrap justify-center gap-2 text-xs text-[#546a7b] mb-6">
                <span className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1">
                  Try removing fuel/type filters
                </span>
                <span className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1">
                  Increase price range
                </span>
              </div>
              <Button
                onClick={clearFilters}
                variant="outline"
                className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
              >
                Clear All Filters
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function VehiclesPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center text-[#393d3f]">
          Loading Catalog...
        </div>
      }
    >
      <VehicleCatalog />
    </Suspense>
  );
}

