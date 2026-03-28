"use client";

import {
  useState,
  useEffect,
  useCallback,
  useRef,
  useSyncExternalStore,
} from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  Search,
  X,
  SlidersHorizontal,
  Menu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ThemeToggle from "@/components/ui/theme-toggle";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetFooter,
} from "@/components/ui/sheet";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import CustomerDashboardNav from "@/components/layout/CustomerDashboardNav";

import { useVehicles } from "@/lib/hooks/useVehicles";
import { useDebounce } from "@/lib/hooks/useDebounce";
import { VehicleCard } from "@/components/vehicles/VehicleCard";
import { VehicleGridSkeleton } from "@/components/vehicles/VehicleCardSkeleton";
import { useExchangeRate } from "@/lib/hooks/useExchangeRate";
import { useAppSelector } from "@/lib/store/store";
import { getAccessToken, getRefreshToken } from "@/lib/auth";

type VehicleSearchParams = Record<string, string | string[] | undefined>;

const ALLOWED_STATUS_VALUES = new Set(["All", "Available", "Sold", "Upcoming"]);
const ALLOWED_FUEL_VALUES = new Set([
  "All",
  "Gasoline",
  "Gasoline/Hybrid",
  "Plugin Hybrid",
  "Diesel",
  "Electric",
]);
const ALLOWED_TYPE_VALUES = new Set([
  "All",
  "SUV",
  "Sedan",
  "Hatchback",
  "Van/minivan",
  "Wagon",
  "Pickup",
  "Coupe",
  "Convertible",
  "Bikes",
  "Machinery",
]);
const ALLOWED_SORT_VALUES = new Set([
  "newest",
  "price_asc",
  "price_desc",
  "year_desc",
  "mileage_asc",
]);
const subscribeHydration = () => () => {};
const getClientHydratedSnapshot = () => true;
const getServerHydratedSnapshot = () => false;

const isThenable = (value: unknown): value is Promise<unknown> =>
  Boolean(value) &&
  (typeof value === "object" || typeof value === "function") &&
  "then" in (value as { then?: unknown });

const getParam = (
  params: VehicleSearchParams | undefined,
  key: string,
  fallback?: string,
) => {
  if (isThenable(params)) {
    return fallback;
  }
  const raw = params?.[key];
  const value = Array.isArray(raw) ? raw[0] : raw;
  return value ?? fallback;
};

const hasParam = (params: VehicleSearchParams | undefined, key: string) =>
  !isThenable(params) &&
  Object.prototype.hasOwnProperty.call(params ?? {}, key);

const toURLSearchParams = (params: VehicleSearchParams | undefined) => {
  if (isThenable(params)) {
    return new URLSearchParams();
  }
  const urlParams = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((entry) => {
        if (entry !== undefined) urlParams.append(key, entry);
      });
    } else if (value !== undefined) {
      urlParams.set(key, value);
    }
  });
  return urlParams;
};

// --- CONSTANTS ---

function VehicleCatalog({
  searchParams,
}: {
  searchParams?: VehicleSearchParams;
}) {
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const hasHydrated = useSyncExternalStore(
    subscribeHydration,
    getClientHydratedSnapshot,
    getServerHydratedSnapshot,
  );
  const hasSession =
    hasHydrated && Boolean(getAccessToken() || getRefreshToken());
  const router = useRouter();

  // -- URL STATE --
  const currentPage = Number(getParam(searchParams, "page", "1")) || 1;
  const currentSearch = getParam(searchParams, "search", "") || "";
  const rawFuel = getParam(searchParams, "fuel", "All") || "All";
  const currentFuel = ALLOWED_FUEL_VALUES.has(rawFuel) ? rawFuel : "All";
  const rawStatus = getParam(searchParams, "status", "All") || "All";
  const currentStatus = ALLOWED_STATUS_VALUES.has(rawStatus)
    ? rawStatus
    : "All";
  const rawSort = getParam(searchParams, "sort", "year_desc") || "year_desc";
  const currentSort = ALLOWED_SORT_VALUES.has(rawSort) ? rawSort : "year_desc";
  const rawType = getParam(searchParams, "type", "All") || "All";
  const currentType = ALLOWED_TYPE_VALUES.has(rawType) ? rawType : "All";
  const currentCurrency =
    (getParam(searchParams, "currency", "LKR") as "LKR" | "JPY") || "LKR";

  const { data: exchangeRateData } = useExchangeRate();
  const exchangeRate = exchangeRateData?.rate || 2.25;

  // Advanced Filters URL State
  const priceMaxLimit =
    currentCurrency === "LKR"
      ? 50000000
      : Math.max(1000000, Math.round(50000000 / exchangeRate));
  const parsedMinPrice = Number(getParam(searchParams, "minPrice"));
  const parsedMaxPrice = Number(getParam(searchParams, "maxPrice"));
  const normalizedMinPrice =
    Number.isFinite(parsedMinPrice) && parsedMinPrice > 0
      ? Math.min(parsedMinPrice, priceMaxLimit)
      : 0;
  const normalizedMaxPrice =
    Number.isFinite(parsedMaxPrice) && parsedMaxPrice > 0
      ? Math.min(parsedMaxPrice, priceMaxLimit)
      : priceMaxLimit;
  const currentMinPrice = Math.min(normalizedMinPrice, normalizedMaxPrice);
  const currentMaxPrice = Math.max(normalizedMaxPrice, normalizedMinPrice);
  const minYearLimit = 2000;
  const maxYearLimit = new Date().getFullYear();
  const maxMileageLimit = 200000;
  const parsedMinYear = Number(getParam(searchParams, "minYear"));
  const parsedMaxYear = Number(getParam(searchParams, "maxYear"));
  const normalizedMinYear =
    Number.isFinite(parsedMinYear) && parsedMinYear > 0
      ? Math.max(minYearLimit, Math.min(parsedMinYear, maxYearLimit))
      : minYearLimit;
  const normalizedMaxYear =
    Number.isFinite(parsedMaxYear) && parsedMaxYear > 0
      ? Math.max(minYearLimit, Math.min(parsedMaxYear, maxYearLimit))
      : maxYearLimit;
  const currentMinYear = Math.min(normalizedMinYear, normalizedMaxYear);
  const currentMaxYear = Math.max(normalizedMaxYear, normalizedMinYear);
  const parsedMaxMileage = Number(getParam(searchParams, "maxMileage"));
  const currentMaxMileage =
    Number.isFinite(parsedMaxMileage) && parsedMaxMileage >= 0
      ? Math.max(0, Math.min(parsedMaxMileage, maxMileageLimit))
      : maxMileageLimit;
  const currentTransmission =
    getParam(searchParams, "transmission", "All") || "All";
  const hasTypeParam = hasParam(searchParams, "type");
  const hasYearFilters =
    currentMinYear > minYearLimit || currentMaxYear < maxYearLimit;
  const hasMileageFilter = currentMaxMileage < maxMileageLimit;
  const hasTransmissionFilter = currentTransmission !== "All";
  const hasAdvancedFilters =
    hasYearFilters || hasMileageFilter || hasTransmissionFilter;
  const hasPriceFilters =
    currentMinPrice > 0 || currentMaxPrice < priceMaxLimit;
  const hasAnyFilters =
    Boolean(currentSearch) ||
    currentFuel !== "All" ||
    currentStatus !== "All" ||
    currentType !== "All" ||
    hasPriceFilters ||
    hasAdvancedFilters;

  // -- LOCAL STATE --
  const [searchTerm, setSearchTerm] = useState(currentSearch);
  const debouncedSearch = useDebounce(searchTerm, 500);
  const isSyncingSearchFromUrlRef = useRef(false);

  useEffect(() => {
    setSearchTerm((prev) => {
      if (prev === currentSearch) {
        return prev;
      }
      isSyncingSearchFromUrlRef.current = true;
      return currentSearch;
    });
  }, [currentSearch]);

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
    (
      newParams: Record<string, string | number | undefined>,
      options?: { replace?: boolean },
    ) => {
      const baseParams: Record<string, string | number | undefined> = {
        page: currentPage,
        search: currentSearch || undefined,
        fuel: currentFuel,
        status: currentStatus,
        sort: currentSort,
        currency: currentCurrency,
        minPrice: currentMinPrice > 0 ? currentMinPrice : undefined,
        maxPrice: currentMaxPrice < priceMaxLimit ? currentMaxPrice : undefined,
        minYear: currentMinYear > minYearLimit ? currentMinYear : undefined,
        maxYear: currentMaxYear < maxYearLimit ? currentMaxYear : undefined,
        maxMileage:
          currentMaxMileage < maxMileageLimit ? currentMaxMileage : undefined,
        transmission:
          currentTransmission !== "All" ? currentTransmission : undefined,
        type: hasTypeParam ? currentType : undefined,
      };

      const mergedParams = { ...baseParams, ...newParams };

      // Drop default values from URL so defaults are not treated as active filters.
      if (
        typeof mergedParams.minPrice === "number" &&
        mergedParams.minPrice <= 0
      ) {
        mergedParams.minPrice = undefined;
      }
      if (
        typeof mergedParams.maxPrice === "number" &&
        mergedParams.maxPrice >= priceMaxLimit
      ) {
        mergedParams.maxPrice = undefined;
      }
      if (
        typeof mergedParams.minYear === "number" &&
        mergedParams.minYear <= minYearLimit
      ) {
        mergedParams.minYear = undefined;
      }
      if (
        typeof mergedParams.maxYear === "number" &&
        mergedParams.maxYear >= maxYearLimit
      ) {
        mergedParams.maxYear = undefined;
      }
      if (
        typeof mergedParams.maxMileage === "number" &&
        mergedParams.maxMileage >= maxMileageLimit
      ) {
        mergedParams.maxMileage = undefined;
      }
      if (mergedParams.transmission === "All") {
        mergedParams.transmission = undefined;
      }

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
      const href = `/dashboard/vehicles${query ? `?${query}` : ""}`;
      if (options?.replace) {
        router.replace(href);
        return;
      }
      router.push(href);
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
      hasTypeParam,
      currentType,
      currentCurrency,
      priceMaxLimit,
      minYearLimit,
      maxYearLimit,
      maxMileageLimit,
    ],
  );

  // -- SYNC DEBOUNCE WITH URL --
  useEffect(() => {
    if (debouncedSearch === currentSearch) {
      isSyncingSearchFromUrlRef.current = false;
      return;
    }
    if (isSyncingSearchFromUrlRef.current) {
      return;
    }
    if (debouncedSearch !== searchTerm) {
      return;
    }
    if (debouncedSearch !== currentSearch) {
      void updateFilters({ search: debouncedSearch }, { replace: true });
    }
  }, [debouncedSearch, currentSearch, searchTerm, updateFilters]);

  // -- DATA FETCHING --
  const { data, isLoading, isError, error, refetch } = useVehicles({
    page: currentPage,
    limit: 8,
    search: currentSearch,
    fuel: currentFuel === "All" ? undefined : currentFuel,
    status: currentStatus === "All" ? undefined : currentStatus,
    sort: currentSort,
    minPrice: currentMinPrice,
    maxPrice: currentMaxPrice < priceMaxLimit ? currentMaxPrice : undefined,
    minYear: currentMinYear > minYearLimit ? currentMinYear : undefined,
    maxYear: currentMaxYear < maxYearLimit ? currentMaxYear : undefined,
    maxMileage:
      currentMaxMileage < maxMileageLimit ? currentMaxMileage : undefined,
    transmission:
      currentTransmission !== "All" ? currentTransmission : undefined,
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
    const params = toURLSearchParams(searchParams);
    let changed = false;
    Array.from(params.keys()).forEach((key) => {
      if (key.startsWith("__") || key.startsWith("_rsc")) {
        params.delete(key);
        return;
      }
      if (!allowed.has(key)) {
        params.delete(key);
        changed = true;
      }
    });
    const statusValue = params.get("status");
    if (statusValue && !ALLOWED_STATUS_VALUES.has(statusValue)) {
      params.delete("status");
      changed = true;
    }
    const fuelValue = params.get("fuel");
    if (fuelValue && !ALLOWED_FUEL_VALUES.has(fuelValue)) {
      params.delete("fuel");
      changed = true;
    }
    const typeValue = params.get("type");
    if (typeValue && !ALLOWED_TYPE_VALUES.has(typeValue)) {
      params.delete("type");
      changed = true;
    }
    const sortValue = params.get("sort");
    if (sortValue && !ALLOWED_SORT_VALUES.has(sortValue)) {
      params.delete("sort");
      changed = true;
    }
    if (changed) {
      const query = params.toString();
      router.replace(`/dashboard/vehicles${query ? `?${query}` : ""}`);
    }
  }, [searchParams, router]);

  const applyAdvancedFilters = () => {
    const [minPriceValue, maxPriceValue] =
      priceRange[0] <= priceRange[1]
        ? [priceRange[0], priceRange[1]]
        : [priceRange[1], priceRange[0]];
    const [minYearValue, maxYearValue] =
      yearRange[0] <= yearRange[1]
        ? [yearRange[0], yearRange[1]]
        : [yearRange[1], yearRange[0]];
    updateFilters({
      minPrice: Math.max(0, Math.min(minPriceValue, priceMaxLimit)),
      maxPrice: Math.max(0, Math.min(maxPriceValue, priceMaxLimit)),
      minYear: Math.max(minYearLimit, Math.min(minYearValue, maxYearLimit)),
      maxYear: Math.max(minYearLimit, Math.min(maxYearValue, maxYearLimit)),
      maxMileage: Math.max(0, Math.min(mileageLimit[0], maxMileageLimit)),
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
      maxPrice:
        currentMaxPrice < priceMaxLimit ? convert(currentMaxPrice) : undefined,
    });
  };

  const isAuthed = isAuthenticated || hasSession;

  return (
    <div className="min-h-screen overflow-x-clip bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans dark:bg-slate-950 dark:text-slate-100 flex flex-col">
      {/* Grid Background */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none z-0" />

      {/* Navigation */}
      {isAuthed ? (
        <CustomerDashboardNav />
      ) : (
        <nav className="sticky top-0 z-50 border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md dark:border-slate-700/70 dark:bg-slate-950/85">
          <div className="cd-container h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2"
            >
              <BrandMark className="h-12 w-12" />
              <span className="hidden sm:inline">
                <BrandWordmark />
              </span>
            </Link>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <div className="hidden sm:flex gap-3">
                <Link href="/login">
                  <Button
                    variant="ghost"
                    className="text-[#546a7b] hover:text-[#393d3f] hover:bg-[#c6c5b9]/20 font-mono h-9 dark:text-slate-300 dark:hover:text-slate-100 dark:hover:bg-slate-800"
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
              <Sheet>
                <SheetTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="sm:hidden text-[#546a7b] hover:text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:text-slate-300 dark:hover:text-slate-100 dark:hover:bg-slate-800"
                  >
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Open menu</span>
                  </Button>
                </SheetTrigger>
                <SheetContent
                  side="right"
                  className="w-[88vw] max-w-sm border-l border-[#546a7b]/30 bg-[#fdfdff] p-0 dark:border-slate-700 dark:bg-slate-900"
                >
                  <SheetHeader className="border-b border-[#546a7b]/20 px-5 py-4 text-left dark:border-slate-700">
                    <SheetTitle className="text-[#393d3f] dark:text-slate-100">
                      Menu
                    </SheetTitle>
                  </SheetHeader>
                  <div className="flex flex-col gap-2 px-4 py-4">
                    <SheetClose asChild>
                      <Link
                        href="/dashboard/vehicles"
                        className="rounded-lg px-3 py-2 text-sm font-medium text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                      >
                        Vehicles
                      </Link>
                    </SheetClose>
                    <SheetClose asChild>
                      <Link
                        href="/tax-calculator"
                        className="rounded-lg px-3 py-2 text-sm font-medium text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                      >
                        Tax Calculator
                      </Link>
                    </SheetClose>
                    <SheetClose asChild>
                      <Link
                        href="/about"
                        className="rounded-lg px-3 py-2 text-sm font-medium text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                      >
                        About Us
                      </Link>
                    </SheetClose>
                    <div className="mt-2 grid grid-cols-1 gap-2">
                      <SheetClose asChild>
                        <Link
                          href="/login"
                          className="rounded-lg border border-[#546a7b]/35 px-3 py-2 text-center text-sm font-medium text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                        >
                          Sign In
                        </Link>
                      </SheetClose>
                      <SheetClose asChild>
                        <Link
                          href="/register"
                          className="rounded-lg bg-[#62929e] px-3 py-2 text-center text-sm font-semibold text-[#fdfdff] hover:bg-[#62929e]/90"
                        >
                          Get Access
                        </Link>
                      </SheetClose>
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </nav>
      )}

      {/* Page Header */}
      <header className="relative z-10 pt-12 pb-8 border-b border-[#546a7b]/40 dark:border-slate-700/60">
        <div className="cd-container">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-[#393d3f] mb-2 tracking-tight dark:text-slate-100">
                Vehicle <span className="text-[#62929e]">Catalog</span>
              </h1>
              <p className="text-[#546a7b] max-w-2xl dark:text-slate-300">
                Browse live auctions from USS Tokyo, JAA, and CAI.
              </p>
            </div>

            {hasAnyFilters && (
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
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#546a7b] dark:text-slate-400" />
                <Input
                  placeholder="Search make, model, chassis..."
                  className="pl-10 h-10 bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] focus:border-[#62929e] hover:bg-[#c6c5b9]/30 transition-colors dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-100 dark:placeholder:text-slate-400 dark:hover:bg-slate-800"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {/* Dropdowns & Sheet Trigger */}
              <div className="flex flex-wrap gap-2">
                <div className="flex items-center gap-1 rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-2 py-1 dark:border-slate-600 dark:bg-slate-800/70">
                  <button
                    type="button"
                    onClick={() => handleCurrencyToggle("LKR")}
                    className={`px-2 py-1 text-xs rounded-full transition ${
                      currentCurrency === "LKR"
                        ? "bg-[#62929e] text-[#fdfdff]"
                        : "text-[#546a7b] hover:text-[#393d3f] dark:text-slate-300 dark:hover:text-slate-100"
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
                        : "text-[#546a7b] hover:text-[#393d3f] dark:text-slate-300 dark:hover:text-slate-100"
                    }`}
                  >
                    JPY
                  </button>
                </div>

                <Select
                  value={currentType}
                  onValueChange={(val) => updateFilters({ type: val })}
                >
                  <SelectTrigger className="h-10 w-full sm:w-[140px] bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30 dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f] dark:bg-slate-900 dark:border-slate-700 dark:text-slate-100">
                    <SelectItem value="All">All Types</SelectItem>
                    <SelectItem value="SUV">SUV</SelectItem>
                    <SelectItem value="Sedan">Sedan</SelectItem>
                    <SelectItem value="Hatchback">Hatchback</SelectItem>
                    <SelectItem value="Van/minivan">Van/Minivan</SelectItem>
                    <SelectItem value="Wagon">Wagon</SelectItem>
                    <SelectItem value="Pickup">Pickup</SelectItem>
                    <SelectItem value="Coupe">Coupe</SelectItem>
                    <SelectItem value="Convertible">Convertible</SelectItem>
                    <SelectItem value="Bikes">Bikes</SelectItem>
                    <SelectItem value="Machinery">Machinery</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentFuel}
                  onValueChange={(val) => updateFilters({ fuel: val })}
                >
                  <SelectTrigger className="h-10 w-full sm:w-[120px] bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30 dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800">
                    <SelectValue placeholder="Fuel" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f] dark:bg-slate-900 dark:border-slate-700 dark:text-slate-100">
                    <SelectItem value="All">All Fuels</SelectItem>
                    <SelectItem value="Gasoline">Gasoline</SelectItem>
                    <SelectItem value="Gasoline/Hybrid">
                      Gasoline/Hybrid
                    </SelectItem>
                    <SelectItem value="Plugin Hybrid">Plugin Hybrid</SelectItem>
                    <SelectItem value="Diesel">Diesel</SelectItem>
                    <SelectItem value="Electric">Electric</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentStatus}
                  onValueChange={(val) => updateFilters({ status: val })}
                >
                  <SelectTrigger className="h-10 w-full sm:w-[120px] bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30 dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f] dark:bg-slate-900 dark:border-slate-700 dark:text-slate-100">
                    <SelectItem value="All">All Status</SelectItem>
                    <SelectItem value="Available">Available</SelectItem>
                    <SelectItem value="Upcoming">Upcoming</SelectItem>
                    <SelectItem value="Sold">Sold</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentSort}
                  onValueChange={(val) => updateFilters({ sort: val })}
                >
                  <SelectTrigger className="h-10 w-full sm:w-[160px] bg-[#c6c5b9]/20 border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30 dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800">
                    <SelectValue placeholder="Sort By" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#fdfdff] border-[#546a7b]/65 text-[#393d3f] dark:bg-slate-900 dark:border-slate-700 dark:text-slate-100">
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
                      className="h-10 w-full sm:w-auto border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/30 hover:text-[#62929e] dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800 dark:hover:text-teal-300"
                    >
                      <SlidersHorizontal className="w-4 h-4 mr-2" /> Filters
                    </Button>
                  </SheetTrigger>
                  <SheetContent className="w-full sm:max-w-[460px] border-l border-slate-200/80 bg-slate-50 p-0 text-slate-900 shadow-[0_24px_60px_rgba(15,23,42,0.35)] dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
                    <SheetHeader className="border-b border-slate-200/80 bg-slate-50/95 px-6 py-5 pr-12 backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
                      <SheetTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                        Advanced Filters
                      </SheetTitle>
                      <SheetDescription className="text-sm text-slate-600 dark:text-slate-300">
                        Refine your search with detail.
                      </SheetDescription>
                    </SheetHeader>

                    <div className="max-h-[calc(100vh-188px)] space-y-4 overflow-y-auto px-5 py-5">
                      <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_24px_rgba(84,106,123,0.08)] dark:border-slate-700 dark:bg-slate-800/70">
                        <div className="flex items-center justify-between gap-3">
                          <Label className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                            Price Range ({currentCurrency})
                          </Label>
                          <span className="rounded-full border border-teal-400/40 bg-teal-50 px-2.5 py-1 text-[11px] font-mono font-semibold text-teal-800 dark:border-teal-300/35 dark:bg-teal-500/15 dark:text-teal-100">
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
                          className="py-2 [&_[data-slot=slider-track]]:bg-slate-300 dark:[&_[data-slot=slider-track]]:bg-slate-700 [&_[data-slot=slider-range]]:bg-teal-600 dark:[&_[data-slot=slider-range]]:bg-teal-400 [&_[data-slot=slider-thumb]]:border-teal-700 dark:[&_[data-slot=slider-thumb]]:border-teal-300 [&_[data-slot=slider-thumb]]:bg-white dark:[&_[data-slot=slider-thumb]]:bg-slate-950 [&_[data-slot=slider-thumb]]:shadow-[0_0_0_4px_rgba(13,148,136,0.2)] dark:[&_[data-slot=slider-thumb]]:shadow-[0_0_0_4px_rgba(45,212,191,0.25)]"
                        />
                        <div className="text-[11px] font-medium text-slate-600 dark:text-slate-300">
                          1 JPY = {exchangeRate.toFixed(2)} LKR
                          {exchangeRateData?.date
                            ? ` | ${exchangeRateData.date}`
                            : ""}
                        </div>
                      </div>

                      <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_24px_rgba(84,106,123,0.08)] dark:border-slate-700 dark:bg-slate-800/70">
                        <div className="flex items-center justify-between gap-3">
                          <Label className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                            Year
                          </Label>
                          <span className="rounded-full border border-teal-400/40 bg-teal-50 px-2.5 py-1 text-[11px] font-mono font-semibold text-teal-800 dark:border-teal-300/35 dark:bg-teal-500/15 dark:text-teal-100">
                            {yearRange[0]} - {yearRange[1]}
                          </span>
                        </div>
                        <Slider
                          min={minYearLimit}
                          max={maxYearLimit}
                          step={1}
                          value={yearRange}
                          onValueChange={setYearRange}
                          className="py-2 [&_[data-slot=slider-track]]:bg-slate-300 dark:[&_[data-slot=slider-track]]:bg-slate-700 [&_[data-slot=slider-range]]:bg-teal-600 dark:[&_[data-slot=slider-range]]:bg-teal-400 [&_[data-slot=slider-thumb]]:border-teal-700 dark:[&_[data-slot=slider-thumb]]:border-teal-300 [&_[data-slot=slider-thumb]]:bg-white dark:[&_[data-slot=slider-thumb]]:bg-slate-950 [&_[data-slot=slider-thumb]]:shadow-[0_0_0_4px_rgba(13,148,136,0.2)] dark:[&_[data-slot=slider-thumb]]:shadow-[0_0_0_4px_rgba(45,212,191,0.25)]"
                        />
                      </div>

                      <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_24px_rgba(84,106,123,0.08)] dark:border-slate-700 dark:bg-slate-800/70">
                        <div className="flex items-center justify-between gap-3">
                          <Label className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                            Max Mileage
                          </Label>
                          <span className="rounded-full border border-teal-400/40 bg-teal-50 px-2.5 py-1 text-[11px] font-mono font-semibold text-teal-800 dark:border-teal-300/35 dark:bg-teal-500/15 dark:text-teal-100">
                            {mileageLimit[0].toLocaleString()} km
                          </span>
                        </div>
                        <Slider
                          min={0}
                          max={maxMileageLimit}
                          step={5000}
                          value={mileageLimit}
                          onValueChange={setMileageLimit}
                          className="py-2 [&_[data-slot=slider-track]]:bg-slate-300 dark:[&_[data-slot=slider-track]]:bg-slate-700 [&_[data-slot=slider-range]]:bg-teal-600 dark:[&_[data-slot=slider-range]]:bg-teal-400 [&_[data-slot=slider-thumb]]:border-teal-700 dark:[&_[data-slot=slider-thumb]]:border-teal-300 [&_[data-slot=slider-thumb]]:bg-white dark:[&_[data-slot=slider-thumb]]:bg-slate-950 [&_[data-slot=slider-thumb]]:shadow-[0_0_0_4px_rgba(13,148,136,0.2)] dark:[&_[data-slot=slider-thumb]]:shadow-[0_0_0_4px_rgba(45,212,191,0.25)]"
                        />
                      </div>

                      <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_24px_rgba(84,106,123,0.08)] dark:border-slate-700 dark:bg-slate-800/70">
                        <Label className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          Transmission
                        </Label>
                        <RadioGroup
                          value={selectedTransmission}
                          onValueChange={setSelectedTransmission}
                          className="grid grid-cols-2 gap-2"
                        >
                          {[
                            { value: "All", label: "Any", id: "t-all" },
                            {
                              value: "Automatic",
                              label: "Automatic",
                              id: "t-at",
                            },
                            { value: "Manual", label: "Manual", id: "t-mt" },
                            { value: "CVT", label: "CVT", id: "t-cvt" },
                          ].map((item) => (
                            <Label
                              key={item.id}
                              htmlFor={item.id}
                              className={`flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2 text-sm transition ${
                                selectedTransmission === item.value
                                  ? "border-teal-500/55 bg-teal-50 text-slate-900 dark:border-teal-300/60 dark:bg-teal-500/20 dark:text-slate-100"
                                  : "border-slate-300 bg-white text-slate-700 hover:border-teal-500/45 hover:bg-teal-50 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-200 dark:hover:border-teal-300/45 dark:hover:bg-teal-500/15"
                              }`}
                            >
                              <RadioGroupItem
                                value={item.value}
                                id={item.id}
                                className="border-slate-500/70 text-teal-700 dark:border-slate-400/70 dark:text-teal-300"
                              />
                              {item.label}
                            </Label>
                          ))}
                        </RadioGroup>
                      </div>
                    </div>

                    <SheetFooter className="border-t border-slate-200/90 bg-slate-50 px-5 py-4 dark:border-slate-700 dark:bg-slate-900">
                      <div className="grid w-full grid-cols-2 gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setPriceRange([0, priceMaxLimit]);
                            setYearRange([minYearLimit, maxYearLimit]);
                            setMileageLimit([maxMileageLimit]);
                            setSelectedTransmission("All");
                          }}
                          className="border-slate-300 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                        >
                          Reset
                        </Button>
                        <Button
                          onClick={applyAdvancedFilters}
                          className="bg-teal-600 font-semibold text-white hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-400"
                        >
                          Apply Filters
                        </Button>
                      </div>
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
                  className="flex-shrink-0 px-3 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/40 hover:bg-[#c6c5b9]/30 hover:border-[#62929e]/50 text-xs font-medium text-[#546a7b] transition-all whitespace-nowrap dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800 dark:hover:border-teal-400/60"
                >
                  {filter.label}
                </button>
              ))}
            </div>

            {hasAnyFilters && (
              <div className="flex flex-wrap gap-2 pt-1 text-xs">
                {currentSearch && (
                  <button
                    onClick={() => updateFilters({ search: "" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f] dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:border-teal-400/60 dark:hover:text-slate-100"
                  >
                    Search: {currentSearch} x
                  </button>
                )}
                {currentFuel !== "All" && (
                  <button
                    onClick={() => updateFilters({ fuel: "All" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f] dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:border-teal-400/60 dark:hover:text-slate-100"
                  >
                    Fuel: {currentFuel} x
                  </button>
                )}
                {currentStatus !== "All" && (
                  <button
                    onClick={() => updateFilters({ status: "All" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f] dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:border-teal-400/60 dark:hover:text-slate-100"
                  >
                    Status: {currentStatus} x
                  </button>
                )}
                {currentType !== "All" && (
                  <button
                    onClick={() => updateFilters({ type: "All" })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f] dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:border-teal-400/60 dark:hover:text-slate-100"
                  >
                    Type: {currentType} x
                  </button>
                )}
                {currentMinPrice > 0 && (
                  <button
                    onClick={() => updateFilters({ minPrice: undefined })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f] dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:border-teal-400/60 dark:hover:text-slate-100"
                  >
                    Min Price x
                  </button>
                )}
                {currentMaxPrice < priceMaxLimit && (
                  <button
                    onClick={() => updateFilters({ maxPrice: undefined })}
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f] dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:border-teal-400/60 dark:hover:text-slate-100"
                  >
                    Max Price x
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
                    className="rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-1 text-[#546a7b] hover:border-[#62929e]/40 hover:text-[#393d3f] dark:bg-slate-800/70 dark:border-slate-600 dark:text-slate-200 dark:hover:border-teal-400/60 dark:hover:text-slate-100"
                  >
                    Advanced Filters x
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative z-10 py-8">
        <div className="cd-container">
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

export default VehicleCatalog;
