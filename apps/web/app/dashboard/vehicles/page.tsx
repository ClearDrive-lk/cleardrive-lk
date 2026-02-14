"use client";

import { useState, Suspense, useEffect, useCallback } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Terminal,
  ChevronLeft,
  ChevronRight,
  Search,
  X,
  SlidersHorizontal,
} from "lucide-react"; // Removed Filter
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

// --- CONSTANTS ---
const QUICK_FILTERS = [
  { label: "Toyota", params: { search: "Toyota" } },
  { label: "Honda", params: { search: "Honda" } },
  { label: "Under 5M", params: { maxPrice: "5000000" } },
  { label: "Hybrid", params: { fuel: "Hybrid" } },
  { label: "SUVs", params: { search: "SUV" } },
  { label: "Electric", params: { fuel: "Electric" } },
  { label: "Luxury > 15M", params: { minPrice: "15000000" } },
];

function VehicleCatalog() {
  const { logout, isLoading: isLogoutLoading } = useLogout();
  const router = useRouter();
  const searchParams = useSearchParams();

  // -- URL STATE --
  const currentPage = Number(searchParams.get("page")) || 1;
  const currentSearch = searchParams.get("search") || "";
  const currentFuel = searchParams.get("fuel") || "All";
  const currentStatus = searchParams.get("status") || "All";
  const currentSort = searchParams.get("sort") || "newest";

  // Advanced Filters URL State
  const currentMinPrice = Number(searchParams.get("minPrice")) || 0;
  const currentMaxPrice = Number(searchParams.get("maxPrice")) || 50000000;
  const currentMinYear = Number(searchParams.get("minYear")) || 2000;
  const currentMaxYear =
    Number(searchParams.get("maxYear")) || new Date().getFullYear();
  const currentMaxMileage = Number(searchParams.get("maxMileage")) || 200000;
  const currentTransmission = searchParams.get("transmission") || "All";

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

  // Sync Sheet State when it opens
  useEffect(() => {
    if (sheetOpen) {
      setPriceRange([currentMinPrice, currentMaxPrice]);
      setYearRange([currentMinYear, currentMaxYear]);
      setMileageLimit([currentMaxMileage]);
      setSelectedTransmission(currentTransmission);
    }
  }, [
    sheetOpen,
    currentMinPrice,
    currentMaxPrice,
    currentMinYear,
    currentMaxYear,
    currentMaxMileage,
    currentTransmission,
  ]);

  // -- HANDLERS --
  const updateFilters = useCallback(
    (newParams: Record<string, string | number | undefined>) => {
      const params = new URLSearchParams(searchParams.toString());

      Object.entries(newParams).forEach(([key, value]) => {
        if (value !== undefined && value !== "" && value !== "All") {
          params.set(key, String(value));
        } else {
          params.delete(key);
        }
      });

      // Reset to page 1 unless page is explicitly changing
      if (!newParams.page) {
        params.set("page", "1");
      }

      router.push(`/dashboard/vehicles?${params.toString()}`);
    },
    [searchParams, router],
  );

  // -- SYNC DEBOUNCE WITH URL --
  useEffect(() => {
    if (debouncedSearch !== currentSearch) {
      updateFilters({ search: debouncedSearch });
    }
  }, [debouncedSearch, currentSearch, updateFilters]);

  // -- DATA FETCHING --
  const { data, isLoading, isError } = useVehicles({
    page: currentPage,
    limit: 8,
    search: currentSearch,
    fuel: currentFuel === "All" ? undefined : currentFuel,
    status: currentStatus === "All" ? undefined : currentStatus,
    sort: currentSort,
    minPrice: currentMinPrice,
    maxPrice: currentMaxPrice === 50000000 ? undefined : currentMaxPrice,
  });

  const vehicles = data?.data || [];
  const totalItems = data?.total || 0;
  const totalPages = Math.ceil(totalItems / 8);

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
    router.push("/dashboard/vehicles");
  };

  const formatCurrency = (val: number) => {
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `${(val / 1000).toFixed(0)}k`;
    return val.toString();
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans flex flex-col">
      {/* Grid Background */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none z-0" />

      {/* Navigation */}
      <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link
            href="/"
            className="font-bold text-xl tracking-tighter flex items-center gap-2"
          >
            <Terminal className="w-5 h-5 text-[#FE7743]" />
            ClearDrive<span className="text-[#FE7743]">.lk</span>
          </Link>
          <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
            <Link
              href="/dashboard"
              className="hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/orders"
              className="hover:text-white transition-colors"
            >
              Orders
            </Link>
            <Link
              href="/dashboard/vehicles"
              className="text-white flex items-center gap-2"
            >
              Vehicles{" "}
              <Badge
                variant="outline"
                className="text-[10px] border-[#FE7743]/20 text-[#FE7743]"
              >
                LIVE
              </Badge>
            </Link>
            <Link
              href="/dashboard/profile"
              className="hover:text-white transition-colors"
            >
              Profile
            </Link>
          </div>
          <Button
            onClick={logout}
            disabled={isLogoutLoading}
            className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold h-9"
          >
            {isLogoutLoading ? "..." : "Sign Out"}
          </Button>
        </div>
      </nav>

      {/* Page Header */}
      <header className="relative z-10 pt-12 pb-8 px-6 border-b border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-2 tracking-tight">
                Vehicle <span className="text-[#FE7743]">Catalog</span>
              </h1>
              <p className="text-gray-400 max-w-2xl">
                Browse live auctions from USS Tokyo, JAA, and CAI.
              </p>
            </div>

            {(currentSearch ||
              currentFuel !== "All" ||
              currentStatus !== "All" ||
              currentMinPrice > 0) && (
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
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <Input
                  placeholder="Search make, model, chassis..."
                  className="pl-10 h-10 bg-white/5 border-white/10 text-white focus:border-[#FE7743] hover:bg-white/10 transition-colors"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {/* Dropdowns & Sheet Trigger */}
              <div className="flex flex-wrap gap-2">
                <Select
                  value={currentFuel}
                  onValueChange={(val) => updateFilters({ fuel: val })}
                >
                  <SelectTrigger className="w-[120px] h-10 bg-white/5 border-white/10 text-white hover:bg-white/10">
                    <SelectValue placeholder="Fuel" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#111] border-white/10 text-white">
                    <SelectItem value="All">All Fuels</SelectItem>
                    <SelectItem value="Petrol">Petrol</SelectItem>
                    <SelectItem value="Hybrid">Hybrid</SelectItem>
                    <SelectItem value="Diesel">Diesel</SelectItem>
                    <SelectItem value="Electric">Electric</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentStatus}
                  onValueChange={(val) => updateFilters({ status: val })}
                >
                  <SelectTrigger className="w-[120px] h-10 bg-white/5 border-white/10 text-white hover:bg-white/10">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#111] border-white/10 text-white">
                    <SelectItem value="All">All Status</SelectItem>
                    <SelectItem value="Live">Live Auction</SelectItem>
                    <SelectItem value="Upcoming">Upcoming</SelectItem>
                    <SelectItem value="Sold">Sold</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={currentSort}
                  onValueChange={(val) => updateFilters({ sort: val })}
                >
                  <SelectTrigger className="w-[160px] h-10 bg-white/5 border-white/10 text-white hover:bg-white/10">
                    <SelectValue placeholder="Sort By" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#111] border-white/10 text-white">
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
                <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
                  <SheetTrigger asChild>
                    <Button
                      variant="outline"
                      className="h-10 border-white/10 text-white hover:bg-white/10 hover:text-[#FE7743]"
                    >
                      <SlidersHorizontal className="w-4 h-4 mr-2" /> Filters
                    </Button>
                  </SheetTrigger>
                  <SheetContent className="bg-[#0A0A0A] border-white/10 text-white overflow-y-auto">
                    <SheetHeader className="mb-6">
                      <SheetTitle className="text-white">
                        Advanced Filters
                      </SheetTitle>
                      <SheetDescription className="text-gray-400">
                        Refine your search with detail.
                      </SheetDescription>
                    </SheetHeader>

                    <div className="space-y-8">
                      {/* Price Range */}
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <Label className="text-sm font-medium">
                            Price Range (LKR)
                          </Label>
                          <span className="text-xs text-[#FE7743] font-mono">
                            {formatCurrency(priceRange[0])} -{" "}
                            {formatCurrency(priceRange[1])}
                          </span>
                        </div>
                        <Slider
                          min={0}
                          max={50000000}
                          step={1000000}
                          value={priceRange}
                          onValueChange={setPriceRange}
                          className="py-4"
                        />
                      </div>

                      <Separator className="bg-white/10" />

                      {/* Year Range */}
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <Label className="text-sm font-medium">Year</Label>
                          <span className="text-xs text-[#FE7743] font-mono">
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

                      <Separator className="bg-white/10" />

                      {/* Mileage */}
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <Label className="text-sm font-medium">
                            Max Mileage
                          </Label>
                          <span className="text-xs text-[#FE7743] font-mono">
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

                      <Separator className="bg-white/10" />

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
                              className="border-white/20 text-[#FE7743]"
                            />
                            <Label htmlFor="t-all" className="text-gray-300">
                              Any
                            </Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem
                              value="AT"
                              id="t-at"
                              className="border-white/20 text-[#FE7743]"
                            />
                            <Label htmlFor="t-at" className="text-gray-300">
                              Automatic (AT)
                            </Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem
                              value="CVT"
                              id="t-cvt"
                              className="border-white/20 text-[#FE7743]"
                            />
                            <Label htmlFor="t-cvt" className="text-gray-300">
                              CVT
                            </Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem
                              value="MT"
                              id="t-mt"
                              className="border-white/20 text-[#FE7743]"
                            />
                            <Label htmlFor="t-mt" className="text-gray-300">
                              Manual (MT)
                            </Label>
                          </div>
                        </RadioGroup>
                      </div>
                    </div>

                    <SheetFooter className="mt-8">
                      <Button
                        onClick={applyAdvancedFilters}
                        className="w-full bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold"
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
              {QUICK_FILTERS.map((filter, index) => (
                <button
                  key={index}
                  onClick={() => updateFilters(filter.params)}
                  className="flex-shrink-0 px-3 py-1.5 rounded-full bg-white/5 border border-white/5 hover:bg-white/10 hover:border-[#FE7743]/50 text-xs font-medium text-gray-300 transition-all whitespace-nowrap"
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative z-10 px-6 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Error State */}
          {isError && (
            <div className="mb-8 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-center">
              Failed to load vehicles. Please try again later.
            </div>
          )}

          {isLoading ? (
            <VehicleGridSkeleton />
          ) : vehicles.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {vehicles.map((vehicle) => (
                  <VehicleCard key={vehicle.id} vehicle={vehicle} />
                ))}
              </div>

              {/* Pagination Controls */}
              <div className="mt-12 flex flex-col sm:flex-row justify-between items-center gap-4 border-t border-white/5 pt-8">
                <span className="text-sm text-gray-500">
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
                    className="border-white/10 text-white hover:bg-white/5 disabled:opacity-30"
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" /> Prev
                  </Button>

                  <div className="px-4 py-1.5 rounded bg-white/5 text-sm font-mono text-gray-300">
                    Page {currentPage} of {totalPages || 1}
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage >= totalPages}
                    onClick={() => updateFilters({ page: currentPage + 1 })}
                    className="border-white/10 text-white hover:bg-white/5 disabled:opacity-30"
                  >
                    Next <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 bg-[#FE7743]/10 rounded-full flex items-center justify-center mb-6">
                <Search className="w-8 h-8 text-[#FE7743]" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">
                No Vehicles Found
              </h3>
              <p className="text-gray-400 max-w-md mx-auto mb-8">
                We couldn&apos;t find any vehicles matching your search
                criteria. Try adjusting your filters or search term.
              </p>
              <Button
                onClick={clearFilters}
                variant="outline"
                className="border-white/10 text-white hover:bg-white/5"
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
        <div className="min-h-screen bg-[#050505] flex items-center justify-center text-white">
          Loading Catalog...
        </div>
      }
    >
      <AuthGuard>
        <VehicleCatalog />
      </AuthGuard>
    </Suspense>
  );
}
