"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import {
  ChevronLeft,
  Car,
  Gauge,
  Timer,
  Share2,
  Mail,
  MapPin,
} from "lucide-react"; // Removed Calendar, Fuel, Phone
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import ThemeToggle from "@/components/ui/theme-toggle";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";
// Removed unused useVehicles
import { apiClient } from "@/lib/api-client";
import { Vehicle } from "@/types/vehicle";
import { useQuery } from "@tanstack/react-query";
import { mapBackendVehicle, normalizeImageUrl } from "@/lib/vehicle-mapper";
import { CostCalculator } from "@/components/vehicles/CostCalculator";
import OrderCreateForm from "@/components/orders/OrderCreateForm";
import { useAppSelector } from "@/lib/store/store";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { getAccessToken, getRefreshToken } from "@/lib/auth";

// Fetch single vehicle helper
const useVehicle = (id: string) => {
  return useQuery<Vehicle>({
    queryKey: ["vehicle", id],
    queryFn: async () => {
      const response = await apiClient.get(`/vehicles/${id}`);
      return mapBackendVehicle(response.data);
    },
    enabled: !!id,
  });
};

const useVehicleImages = (id: string) => {
  return useQuery<string[]>({
    queryKey: ["vehicle-images", id],
    queryFn: async () => {
      const response = await apiClient.get(`/vehicles/${id}/images`);
      const raw = Array.isArray(response.data?.images)
        ? response.data.images
        : [];
      return raw
        .map((img: string) => normalizeImageUrl(img) || null)
        .filter((img: string | null): img is string => Boolean(img));
    },
    enabled: !!id,
  });
};

function VehicleDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const hasSession = Boolean(getAccessToken() || getRefreshToken());
  // Removed unused logout, isLogoutLoading
  const { data: vehicle, isLoading, isError } = useVehicle(id);
  const { data: galleryImages } = useVehicleImages(id);
  const [selectedImageOverride, setSelectedImageOverride] = useState<
    string | null
  >(null);

  const displayImage = selectedImageOverride || vehicle?.imageUrl || null;

  // Formatters
  const formatJPY = new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    maximumSignificantDigits: 3,
  }).format;
  const formatLKR = new Intl.NumberFormat("en-LK", {
    style: "currency",
    currency: "LKR",
    maximumSignificantDigits: 3,
  }).format;
  const formatKm = new Intl.NumberFormat("en-US").format;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center text-[#393d3f]">
        <div className="animate-pulse flex flex-col items-center">
          <Car className="w-12 h-12 text-[#62929e] mb-4 opacity-50" />
          <p className="font-mono text-sm text-[#546a7b]">
            Loading Vehicle Details...
          </p>
        </div>
      </div>
    );
  }

  if (isError || !vehicle) {
    return (
      <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center text-[#393d3f]">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Vehicle Not Found</h2>
          <Button
            onClick={() => router.back()}
            variant="outline"
            className="border-[#546a7b]/65"
          >
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  // Determine images (Mocking multiple images if api only returns one)
  const images = galleryImages?.length
    ? galleryImages
    : vehicle.imageUrl
      ? [vehicle.imageUrl]
      : [];

  const hasPrice = Number.isFinite(vehicle.priceJPY) && vehicle.priceJPY > 0;
  const estDuty = hasPrice ? vehicle.estimatedLandedCostLKR * 0.3 : 0;

  const contactAgent = () => {
    const subject = encodeURIComponent(
      `Inquiry about ${vehicle.year} ${vehicle.make} ${vehicle.model} (${vehicle.lotNumber})`,
    );
    window.location.href = `mailto:sales@cleardrive.lk?subject=${subject}`;
  };

  return (
    <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
      {/* Grid Background */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none z-0" />

      {/* Navigation */}
      <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="cd-container h-16 flex items-center justify-between">
          <Link
            href={isAuthenticated || hasSession ? "/dashboard" : "/"}
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
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
          </div>
        </div>
      </nav>

      <main className="flex-1 relative z-10 cd-container py-8">
        {/* Breadcrumb / Back */}
        <Button
          onClick={() => router.back()}
          variant="ghost"
          className="mb-6 pl-0 hover:bg-transparent hover:text-[#62929e] text-[#546a7b]"
        >
          <ChevronLeft className="w-4 h-4 mr-2" /> Back to Catalog
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* LEFT COLUMN: Gallery */}
          <div className="space-y-4">
            <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-gray-900 border border-[#546a7b]/65">
              {displayImage ? (
                <Image
                  src={displayImage}
                  alt="Vehicle Main"
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-gray-700">
                  <Car className="w-16 h-16 opacity-20" />
                </div>
              )}

              {/* Tags Overlay */}
              <div className="absolute top-4 left-4 flex gap-2">
                <Badge className="bg-[#62929e] text-[#fdfdff] font-bold border-0">
                  Grade {vehicle.grade}
                </Badge>
                {vehicle.condition === "New" && (
                  <Badge className="bg-green-500 text-[#393d3f] font-bold border-0">
                    NEW
                  </Badge>
                )}
              </div>
            </div>

            {/* Thumbnails */}
            {images.length > 0 && (
              <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-none">
                {images.map((img, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedImageOverride(img)}
                    className={`relative w-24 h-16 rounded overflow-hidden border-2 transition-all flex-shrink-0 ${
                      displayImage === img
                        ? "border-[#62929e]"
                        : "border-transparent opacity-70 hover:opacity-100"
                    }`}
                  >
                    <Image
                      src={img}
                      alt="Thumbnail"
                      fill
                      className="object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: Details */}
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-[#393d3f] mb-2">
                {vehicle.year} {vehicle.make}{" "}
                <span className="text-[#62929e]">{vehicle.model}</span>
              </h1>
              <p className="text-xl text-[#546a7b]">
                {vehicle.trim} ({vehicle.chassisCode})
              </p>

              <div className="flex items-center gap-4 mt-4 text-sm font-mono text-[#546a7b]">
                <span className="flex items-center gap-1">
                  <Timer className="w-4 h-4" /> Lot #{vehicle.lotNumber}
                </span>
                <span className="w-1 h-1 bg-gray-700 rounded-full" />
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" /> {vehicle.location || "Japan"}
                </span>
              </div>
            </div>

            <Separator className="bg-[#c6c5b9]/30" />

            {/* Price Card */}
            <Card className="bg-[#c6c5b9]/20 border-[#546a7b]/65 overflow-hidden">
              <CardContent className="p-6">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-[#546a7b] text-sm">
                    Estimated Landed Cost
                  </span>
                  <span className="text-3xl font-bold text-[#393d3f]">
                    {hasPrice
                      ? formatLKR(vehicle.estimatedLandedCostLKR)
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm text-[#546a7b] font-mono mb-6">
                  <span>
                    Current Bid:{" "}
                    {hasPrice ? formatJPY(vehicle.priceJPY) : "N/A"}
                  </span>
                  <span>
                    Est. Duty: {hasPrice ? formatLKR(estDuty) : "N/A"}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Button
                    onClick={contactAgent}
                    className="bg-[#62929e] hover:bg-[#62929e]/90 text-[#fdfdff] font-bold h-12"
                  >
                    <Mail className="w-4 h-4 mr-2" /> Contact Agent
                  </Button>
                  <Button
                    variant="outline"
                    className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20 h-12"
                  >
                    <Share2 className="w-4 h-4 mr-2" /> Share
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div id="cost-calculator" className="scroll-mt-24">
              <CostCalculator
                vehicleId={vehicle.id}
                priceJPY={vehicle.priceJPY}
              />
            </div>

            <div id="order-create" className="scroll-mt-24">
              {isAuthenticated ? (
                <OrderCreateForm
                  vehicleId={vehicle.id}
                  estimatedTotalLkr={vehicle.estimatedLandedCostLKR}
                />
              ) : (
                <Card className="border-[#546a7b]/65 bg-[#fdfdff]">
                  <CardContent className="p-6 space-y-3">
                    <h3 className="text-lg font-bold text-[#393d3f]">
                      Sign in to reserve this vehicle
                    </h3>
                    <p className="text-sm text-[#546a7b]">
                      You can browse inventory without an account, but you need
                      to sign in to create an order.
                    </p>
                    <div className="flex gap-3">
                      <Button asChild className="bg-[#62929e] text-[#fdfdff]">
                        <Link href="/login">Sign In</Link>
                      </Button>
                      <Button
                        asChild
                        variant="outline"
                        className="border-[#546a7b]/65 text-[#393d3f] hover:bg-[#c6c5b9]/20"
                      >
                        <Link href="/register">Create Account</Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Specs Table */}
            <div>
              <h3 className="text-lg font-bold text-[#393d3f] mb-4 flex items-center gap-2">
                <Gauge className="w-5 h-5 text-[#62929e]" /> Specifications
              </h3>
              <div className="rounded-lg border border-[#546a7b]/65 overflow-hidden">
                <Table>
                  <TableBody>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Stock No
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.lotNumber}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Make
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.make}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Model
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.model}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Year
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.year}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        First Registration
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.firstRegistrationDate
                          ? String(vehicle.firstRegistrationDate)
                          : "N/A"}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Type
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.vehicleType || "N/A"}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Mileage
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {formatKm(vehicle.mileage)} km
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Engine
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.engineCC} cc
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Fuel
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.fuel}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Transmission
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.transmission}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Steering
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.steering || "N/A"}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Drive
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.drive || "N/A"}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Seats / Doors
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.seats || "N/A"} / {vehicle.doors || "N/A"}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Color
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.color || "N/A"}
                      </TableCell>
                    </TableRow>
                    <TableRow className="border-[#546a7b]/40 hover:bg-[#c6c5b9]/20">
                      <TableCell className="font-medium text-[#546a7b]">
                        Location
                      </TableCell>
                      <TableCell className="text-[#393d3f] text-right">
                        {vehicle.location || "N/A"}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-bold text-[#393d3f]">
                Other Details
              </h3>
              <div className="rounded-lg border border-[#546a7b]/65 p-4 bg-[#c6c5b9]/20">
                <p className="text-sm font-semibold text-[#546a7b] mb-2">
                  Options
                </p>
                <p className="text-sm text-gray-200 whitespace-pre-wrap">
                  {vehicle.options || "N/A"}
                </p>
              </div>
              <div className="rounded-lg border border-[#546a7b]/65 p-4 bg-[#c6c5b9]/20">
                <p className="text-sm font-semibold text-[#546a7b] mb-2">
                  Other Remarks
                </p>
                <p className="text-sm text-gray-200 whitespace-pre-wrap">
                  {vehicle.otherRemarks || "N/A"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function VehicleDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center text-[#393d3f]">
          Loading...
        </div>
      }
    >
      <VehicleDetail />
    </Suspense>
  );
}
