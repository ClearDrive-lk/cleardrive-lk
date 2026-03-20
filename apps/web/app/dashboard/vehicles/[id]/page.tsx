"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  CalendarDays,
  Car,
  ChevronLeft,
  CircleCheckBig,
  Clock3,
  Gauge,
  Mail,
  MapPin,
  Share2,
  ShieldCheck,
  Timer,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ThemeToggle from "@/components/ui/theme-toggle";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { CostCalculator } from "@/components/vehicles/CostCalculator";
import OrderCreateForm from "@/components/orders/OrderCreateForm";
import CustomerDashboardNav from "@/components/layout/CustomerDashboardNav";
import { apiClient } from "@/lib/api-client";
import { getAccessToken, getRefreshToken } from "@/lib/auth";
import { mapBackendVehicle, normalizeImageUrl } from "@/lib/vehicle-mapper";
import { useAppSelector } from "@/lib/store/store";
import { Vehicle } from "@/types/vehicle";

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

const useVehicle = (id: string) =>
  useQuery<Vehicle>({
    queryKey: ["vehicle", id],
    queryFn: async () => {
      const response = await apiClient.get(`/vehicles/${id}`);
      return mapBackendVehicle(response.data);
    },
    enabled: Boolean(id),
  });

const useVehicleImages = (id: string) =>
  useQuery<string[]>({
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
    enabled: Boolean(id),
  });

function VehicleDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const [hasSession, setHasSession] = useState(false);
  const [authReady, setAuthReady] = useState(false);
  const isAuthed = authReady && (isAuthenticated || hasSession);

  const { data: vehicle, isLoading, isError } = useVehicle(id);
  const { data: galleryImages } = useVehicleImages(id);

  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [shareCopied, setShareCopied] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    setHasSession(Boolean(getAccessToken() || getRefreshToken()));
    setAuthReady(true);
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 30000);
    return () => window.clearInterval(interval);
  }, []);

  const images = useMemo(() => {
    if (galleryImages?.length) return galleryImages;
    if (vehicle?.imageUrl) return [vehicle.imageUrl];
    return [];
  }, [galleryImages, vehicle?.imageUrl]);

  useEffect(() => {
    if (!images.length) {
      setSelectedImage(null);
      return;
    }
    setSelectedImage((current) =>
      current && images.includes(current) ? current : images[0],
    );
  }, [images]);

  const auctionEnd = useMemo(() => {
    if (!vehicle?.endTime) return null;
    const parsed = new Date(vehicle.endTime);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }, [vehicle?.endTime]);

  const timeToEndLabel = useMemo(() => {
    if (!auctionEnd) return "Schedule unavailable";
    const diffMs = auctionEnd.getTime() - now;
    if (diffMs <= 0) return "Auction closed";

    const totalMinutes = Math.floor(diffMs / 60000);
    const days = Math.floor(totalMinutes / (60 * 24));
    const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
    const minutes = totalMinutes % 60;

    if (days > 0) return `${days}d ${hours}h remaining`;
    if (hours > 0) return `${hours}h ${minutes}m remaining`;
    return `${minutes}m remaining`;
  }, [auctionEnd, now]);

  const highlightChips = useMemo(() => {
    if (!vehicle) return [];

    const raw = `${vehicle.options ?? ""}\n${vehicle.otherRemarks ?? ""}`;
    const parsed = raw
      .split(/[\n,;|]+/)
      .map((item) => item.trim())
      .filter((item) => item.length > 2 && item.toLowerCase() !== "n/a");
    const unique = Array.from(new Set(parsed)).slice(0, 6);
    if (unique.length) return unique;

    return [
      vehicle.vehicleType || "Vehicle listing",
      `${vehicle.fuel} powertrain`,
      `${vehicle.transmission} transmission`,
      vehicle.fuel.toLowerCase().includes("electric")
        ? "Electric drivetrain"
        : vehicle.engineCC && vehicle.engineCC > 0
          ? `${vehicle.engineCC}cc engine`
          : "Engine spec pending",
      `${vehicle.year} model year`,
    ];
  }, [
    vehicle?.engineCC,
    vehicle?.fuel,
    vehicle?.options,
    vehicle?.otherRemarks,
    vehicle?.transmission,
    vehicle?.vehicleType,
    vehicle?.year,
  ]);

  const hasPrice = Boolean(
    vehicle && Number.isFinite(vehicle.priceJPY) && vehicle.priceJPY > 0,
  );
  const isAvailable = vehicle?.status === "Live";
  const isElectric = vehicle?.fuel.toLowerCase().includes("electric");
  const engineLabel = isElectric
    ? "Electric drivetrain"
    : typeof vehicle?.engineCC === "number" && vehicle.engineCC > 0
      ? `${vehicle.engineCC} cc`
      : "Spec pending";
  const canCreateOrder = isAuthed && isAvailable;
  const estDuty =
    hasPrice && vehicle ? Math.round(vehicle.estimatedLandedCostLKR * 0.3) : 0;
  const bidLabel = hasPrice ? formatJPY(vehicle.priceJPY) : "Bid pending";
  const landedLabel = hasPrice
    ? formatLKR(vehicle.estimatedLandedCostLKR)
    : "Awaiting bid";
  const dutyLabel = hasPrice ? formatLKR(estDuty) : "Pending";
  const displayImage = selectedImage || images[0] || null;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[hsl(var(--background))] flex items-center justify-center">
        <div className="text-center space-y-3">
          <Car className="mx-auto h-10 w-10 animate-pulse text-[hsl(var(--primary))]" />
          <p className="text-sm text-[hsl(var(--secondary))]">
            Loading vehicle command center...
          </p>
        </div>
      </div>
    );
  }

  if (isError || !vehicle) {
    return (
      <div className="min-h-screen bg-[hsl(var(--background))] flex items-center justify-center p-6">
        <div className="w-full max-w-md rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 text-center shadow-[0_16px_32px_rgba(15,23,42,0.16)]">
          <h2 className="text-2xl font-bold">Vehicle Not Found</h2>
          <p className="mt-2 text-sm text-[hsl(var(--secondary))]">
            This listing may have moved or is no longer available.
          </p>
          <Button onClick={() => router.back()} className="mt-5">
            Back to Catalog
          </Button>
        </div>
      </div>
    );
  }

  const contactAgent = () => {
    const subject = encodeURIComponent(
      `Inquiry about ${vehicle.year} ${vehicle.make} ${vehicle.model} (${vehicle.lotNumber})`,
    );
    window.location.href = `mailto:sales@cleardrive.lk?subject=${subject}`;
  };

  const shareVehicle = async () => {
    const title = `${vehicle.year} ${vehicle.make} ${vehicle.model}`;
    const text = `Check this vehicle on ClearDrive: ${title}`;
    const url = window.location.href;

    if (navigator.share) {
      try {
        await navigator.share({ title, text, url });
        return;
      } catch {
        // Fall back to clipboard below.
      }
    }

    try {
      await navigator.clipboard.writeText(url);
      setShareCopied(true);
      window.setTimeout(() => setShareCopied(false), 1400);
    } catch {
      setShareCopied(false);
    }
  };

  const summaryStats = [
    { label: "Mileage", value: `${formatKm(vehicle.mileage)} km`, icon: Gauge },
    { label: "Engine", value: engineLabel, icon: Car },
    {
      label: "Transmission",
      value: vehicle.transmission || "N/A",
      icon: Timer,
    },
    { label: "Fuel", value: vehicle.fuel || "N/A", icon: Zap },
  ];

  const readinessItems = [
    { label: "Landed cost estimate available", done: hasPrice },
    {
      label: "Core specs complete",
      done: Boolean(vehicle.make && vehicle.model && vehicle.year),
    },
    { label: "Gallery ready", done: images.length > 0 },
    { label: "Order placement available", done: canCreateOrder },
  ];

  const specRows = [
    ["Stock No", vehicle.lotNumber || "N/A"],
    ["Make", vehicle.make || "N/A"],
    ["Model", vehicle.model || "N/A"],
    ["Year", String(vehicle.year || "N/A")],
    ["Type", vehicle.vehicleType || "N/A"],
    ["Mileage", `${formatKm(vehicle.mileage || 0)} km`],
    ["Engine", engineLabel],
    ["Fuel", vehicle.fuel || "N/A"],
    ["Transmission", vehicle.transmission || "N/A"],
    ["Color", vehicle.color || "N/A"],
    ["Location", vehicle.location || "N/A"],
  ] as const;

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))] font-sans">
      <div className="fixed inset-0 -z-20 bg-[hsl(var(--background))]" />
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_10%_0%,rgba(31,158,179,0.16),transparent_45%),radial-gradient(circle_at_88%_6%,rgba(108,136,170,0.18),transparent_42%)]" />
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[linear-gradient(to_right,rgba(84,106,123,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(84,106,123,0.08)_1px,transparent_1px)] bg-[size:42px_42px] dark:opacity-70" />

      {isAuthed ? (
        <CustomerDashboardNav />
      ) : (
        <nav className="sticky top-0 z-50 border-b border-[hsl(var(--border))] bg-[hsl(var(--background))]/85 backdrop-blur-md">
          <div className="cd-container h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2"
            >
              <BrandMark className="h-8 w-8 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--primary))]/15" />
              <BrandWordmark />
            </Link>
            <div className="hidden md:flex gap-8 text-sm font-medium text-[hsl(var(--secondary))]">
              <Link href="/" className="hover:text-[hsl(var(--foreground))]">
                Home
              </Link>
              <Link
                href="/dashboard/vehicles"
                className="flex items-center gap-2 text-[hsl(var(--foreground))]"
              >
                Vehicles
                <Badge variant="outline" className="text-[10px]">
                  LIVE
                </Badge>
              </Link>
            </div>
            <ThemeToggle />
          </div>
        </nav>
      )}

      <main className="cd-container relative z-10 py-6 md:py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Button
            onClick={() => router.back()}
            variant="ghost"
            className="pl-0 text-[hsl(var(--secondary))] hover:bg-transparent hover:text-[hsl(var(--foreground))]"
          >
            <ChevronLeft className="mr-1 h-4 w-4" />
            Back to Catalog
          </Button>
          <div className="flex items-center gap-2 text-xs text-[hsl(var(--secondary))]">
            <MapPin className="h-3.5 w-3.5" />
            {vehicle.location || "Japan"} Auction Floor
          </div>
        </div>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(340px,0.85fr)]">
          <div className="space-y-4">
            <article className="overflow-hidden rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 shadow-[0_20px_50px_rgba(12,23,38,0.2)]">
              <div className="relative h-[250px] sm:h-[340px] xl:h-[430px]">
                {displayImage ? (
                  <Image
                    src={displayImage}
                    alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
                    fill
                    priority
                    className="object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Car className="h-16 w-16 text-[hsl(var(--secondary))] opacity-40" />
                  </div>
                )}

                <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-black/5 to-transparent" />

                <div className="absolute left-3 top-3 flex flex-wrap gap-2">
                  <Badge className="rounded-full border border-white/30 bg-black/45 text-white">
                    Grade {vehicle.grade || "N/A"}
                  </Badge>
                  <Badge className="rounded-full border border-white/30 bg-black/45 text-white">
                    {vehicle.status}
                  </Badge>
                  {vehicle.condition === "New" ? (
                    <Badge className="rounded-full border border-emerald-300/40 bg-emerald-500/80 text-white">
                      NEW
                    </Badge>
                  ) : null}
                </div>

                <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between gap-3 text-white/95">
                  <p className="rounded-full bg-black/35 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em]">
                    Lot #{vehicle.lotNumber || "N/A"}
                  </p>
                  <p className="text-xs font-medium">
                    {vehicle.location || "Japan"}
                  </p>
                </div>
              </div>

              {images.length > 1 ? (
                <div className="border-t border-[hsl(var(--border))] p-3">
                  <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
                    {images.map((img, idx) => {
                      const active = displayImage === img;
                      return (
                        <button
                          key={`${img}-${idx}`}
                          onClick={() => setSelectedImage(img)}
                          className={`relative h-16 w-24 flex-shrink-0 overflow-hidden rounded-lg border transition ${
                            active
                              ? "border-[hsl(var(--primary))] ring-2 ring-[hsl(var(--primary))]/30"
                              : "border-[hsl(var(--border))] opacity-80 hover:opacity-100"
                          }`}
                          aria-label={`View image ${idx + 1}`}
                        >
                          <Image
                            src={img}
                            alt={`Vehicle image ${idx + 1}`}
                            fill
                            className="object-cover"
                          />
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}
            </article>

            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {summaryStats.map((item) => (
                <article
                  key={item.label}
                  className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/85 p-3 shadow-[0_8px_24px_rgba(15,23,42,0.1)]"
                >
                  <div className="mb-2 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[hsl(var(--primary))]/12 text-[hsl(var(--primary))]">
                    <item.icon className="h-4 w-4" />
                  </div>
                  <p className="text-[10px] uppercase tracking-[0.16em] text-[hsl(var(--secondary))]">
                    {item.label}
                  </p>
                  <p className="mt-1 text-sm font-semibold">{item.value}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-5 shadow-[0_20px_45px_rgba(12,23,38,0.16)] md:p-6">
              <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
                {vehicle.year} {vehicle.make}{" "}
                <span className="text-[hsl(var(--primary))]">
                  {vehicle.model}
                </span>
              </h1>
              <p className="mt-1 text-sm text-[hsl(var(--secondary))] md:text-base">
                {vehicle.trim || "Trim unavailable"}{" "}
                {vehicle.chassisCode ? `(${vehicle.chassisCode})` : ""}
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                {highlightChips.map((chip) => (
                  <span
                    key={chip}
                    className="rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--muted))]/25 px-3 py-1 text-xs font-medium"
                  >
                    {chip}
                  </span>
                ))}
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--muted))]/22 p-3">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--secondary))]">
                    Estimated Landed
                  </p>
                  <p className="mt-1 text-xl font-bold">{landedLabel}</p>
                  <p className="mt-1 text-xs text-[hsl(var(--secondary))]">
                    Duty estimate: {dutyLabel}
                  </p>
                </div>
                <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--muted))]/22 p-3">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--secondary))]">
                    Current Bid
                  </p>
                  <p className="mt-1 text-xl font-bold">{bidLabel}</p>
                  <p className="mt-1 text-xs text-[hsl(var(--secondary))]">
                    Last refreshed with live feed
                  </p>
                </div>
              </div>

              <div className="mt-4 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--muted))]/20 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--secondary))]">
                      Auction End
                    </p>
                    <p className="mt-1 text-sm font-semibold">
                      {auctionEnd ? auctionEnd.toLocaleString() : "N/A"}
                    </p>
                    <p className="mt-1 inline-flex items-center gap-1.5 text-xs text-[hsl(var(--secondary))]">
                      <Clock3 className="h-3.5 w-3.5" />
                      {timeToEndLabel}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--secondary))]">
                      First Registration
                    </p>
                    <p className="mt-1 inline-flex items-center gap-1.5 text-sm font-semibold">
                      <CalendarDays className="h-3.5 w-3.5 text-[hsl(var(--primary))]" />
                      {vehicle.firstRegistrationDate
                        ? new Date(
                            vehicle.firstRegistrationDate,
                          ).toLocaleDateString()
                        : "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <Button onClick={contactAgent} className="h-11 font-semibold">
                  <Mail className="mr-2 h-4 w-4" />
                  Contact Agent
                </Button>
                <Button
                  variant="outline"
                  onClick={shareVehicle}
                  className="h-11 font-semibold"
                >
                  <Share2 className="mr-2 h-4 w-4" />
                  {shareCopied ? "Link Copied" : "Share Vehicle"}
                </Button>
              </div>
            </article>

            <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-5">
              <h2 className="mb-3 text-base font-semibold">
                Auction Readiness
              </h2>
              <div className="space-y-2">
                {readinessItems.map((item) => (
                  <div
                    key={item.label}
                    className="flex items-center justify-between rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--muted))]/20 px-3 py-2"
                  >
                    <span className="text-sm">{item.label}</span>
                    {item.done ? (
                      <CircleCheckBig className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <ShieldCheck className="h-4 w-4 text-amber-500" />
                    )}
                  </div>
                ))}
              </div>
            </article>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-2">
          <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-1 shadow-[0_14px_30px_rgba(15,23,42,0.12)]">
            <CostCalculator
              vehicleId={vehicle.id}
              priceJPY={vehicle.priceJPY}
            />
          </article>

          <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-1 shadow-[0_14px_30px_rgba(15,23,42,0.12)]">
            {canCreateOrder ? (
              <OrderCreateForm
                vehicleId={vehicle.id}
                estimatedTotalLkr={vehicle.estimatedLandedCostLKR}
              />
            ) : !isAuthed ? (
              <div className="p-6 space-y-3">
                <h3 className="text-lg font-bold">
                  Sign in to reserve this vehicle
                </h3>
                <p className="text-sm text-[hsl(var(--secondary))]">
                  Browse freely, then sign in when you are ready to create an
                  order.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button asChild>
                    <Link href="/login">Sign In</Link>
                  </Button>
                  <Button asChild variant="outline">
                    <Link href="/register">Create Account</Link>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="p-6 space-y-3">
                <h3 className="text-lg font-bold">Vehicle not available</h3>
                <p className="text-sm text-[hsl(var(--secondary))]">
                  This listing is currently marked as {vehicle.status}. Check
                  back later or contact an agent to request availability.
                </p>
                <Button onClick={contactAgent}>
                  <Mail className="mr-2 h-4 w-4" />
                  Contact Agent
                </Button>
              </div>
            )}
          </article>
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-5 md:p-6">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-bold">
              <Gauge className="h-5 w-5 text-[hsl(var(--primary))]" />
              Vehicle Specifications
            </h2>
            <div className="overflow-hidden rounded-xl border border-[hsl(var(--border))]">
              <Table>
                <TableBody>
                  {specRows.map(([label, value]) => (
                    <TableRow
                      key={label}
                      className="border-[hsl(var(--border))]/60"
                    >
                      <TableCell className="font-medium text-[hsl(var(--secondary))]">
                        {label}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {value}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </article>

          <div className="space-y-5">
            <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-5">
              <h3 className="text-base font-semibold">Options</h3>
              <p className="mt-2 whitespace-pre-wrap text-sm text-[hsl(var(--secondary))]">
                {vehicle.options || "N/A"}
              </p>
            </article>

            <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-5">
              <h3 className="text-base font-semibold">Other Remarks</h3>
              <p className="mt-2 whitespace-pre-wrap text-sm text-[hsl(var(--secondary))]">
                {vehicle.otherRemarks || "N/A"}
              </p>
            </article>

            <article className="rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]/90 p-5">
              <h3 className="text-base font-semibold">Need Assistance?</h3>
              <p className="mt-2 text-sm text-[hsl(var(--secondary))]">
                Talk with our team for inspection interpretation, import taxes,
                and order guidance.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={contactAgent}>
                  <Mail className="mr-2 h-4 w-4" />
                  Email Support
                </Button>
                <Button variant="outline">
                  <MapPin className="mr-2 h-4 w-4" />
                  Colombo Ops
                </Button>
              </div>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}

export default function VehicleDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[hsl(var(--background))] flex items-center justify-center text-[hsl(var(--secondary))]">
          Loading...
        </div>
      }
    >
      <VehicleDetail />
    </Suspense>
  );
}
