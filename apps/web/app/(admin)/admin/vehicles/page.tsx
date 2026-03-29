"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { isAxiosError } from "axios";
import {
  Loader2,
  RefreshCcw,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { VehicleCard } from "@/components/vehicles/VehicleCard";
import { VehicleGridSkeleton } from "@/components/vehicles/VehicleCardSkeleton";
import { useVehicles } from "@/lib/hooks/useVehicles";
import { apiClient } from "@/lib/api-client";
import { useToast } from "@/lib/hooks/use-toast";

const PAGE_SIZE = 12;

function statusToFilter(status: string) {
  if (status === "live") return "Available";
  if (status === "upcoming") return "Upcoming";
  if (status === "sold") return "Sold";
  return undefined;
}

export default function AdminVehiclesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);
  const search = searchParams.get("search") ?? "";
  const status = searchParams.get("status") ?? "all";
  const [cleanupPending, setCleanupPending] = useState(false);
  const [deletePendingId, setDeletePendingId] = useState<string | null>(null);

  const query = useVehicles({
    page,
    limit: PAGE_SIZE,
    search,
    status: statusToFilter(status),
    sort: "newest",
  });

  const vehicles = query.data?.data ?? [];
  const totalItems = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));

  const summary = useMemo(
    () => [
      {
        label: "Visible Listings",
        value: totalItems.toLocaleString(),
        hint: "Admin catalog access",
      },
      {
        label: "Page Window",
        value: `${vehicles.length}/${PAGE_SIZE}`,
        hint: "Listings loaded now",
      },
      {
        label: "Image Hygiene",
        value: cleanupPending ? "Running" : "Ready",
        hint: "Cleanup trigger available",
      },
    ],
    [cleanupPending, totalItems, vehicles.length],
  );

  const updateParams = (updates: Record<string, string | undefined>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, value]) => {
      if (!value || value === "all") {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    });
    if (!("page" in updates)) {
      params.set("page", "1");
    }
    const queryString = params.toString();
    router.push(`/admin/vehicles${queryString ? `?${queryString}` : ""}`);
  };

  const runCleanup = async () => {
    setCleanupPending(true);
    try {
      const response = await apiClient.post("/vehicles/cleanup-images");
      const message =
        typeof response.data?.message === "string"
          ? response.data.message
          : "Vehicle image cleanup started.";
      toast({
        title: "Cleanup started",
        description: message,
        variant: "success",
      });
    } catch (error: unknown) {
      toast({
        title: "Cleanup failed",
        description: isAxiosError(error)
          ? ((error.response?.data as { detail?: string } | undefined)
              ?.detail ?? "Failed to start cleanup.")
          : "Failed to start cleanup.",
        variant: "destructive",
      });
    } finally {
      setCleanupPending(false);
    }
  };

  const handleDeleteVehicle = async (vehicleId: string, label: string) => {
    const confirmed = window.confirm(
      `Delete ${label} from the catalog? This cannot be undone.`,
    );
    if (!confirmed) return;

    setDeletePendingId(vehicleId);
    try {
      await apiClient.delete(`/vehicles/${vehicleId}`);
      toast({
        title: "Vehicle deleted",
        description: `${label} was removed from the catalog.`,
        variant: "success",
      });
      await query.refetch();
    } catch (error: unknown) {
      toast({
        title: "Delete failed",
        description: isAxiosError(error)
          ? ((error.response?.data as { detail?: string } | undefined)
              ?.detail ?? "Failed to delete vehicle.")
          : "Failed to delete vehicle.",
        variant: "destructive",
      });
    } finally {
      setDeletePendingId(null);
    }
  };

  return (
    <div className="cd-container space-y-6 py-6 text-[#393d3f]">
      <header className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#62929e]">
              Vehicle Operations
            </p>
            <h1 className="mt-2 text-3xl font-semibold">
              Admin Vehicle Catalog
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-[#546a7b]">
              Review live inventory, open any listing as admin, and trigger
              cleanup for placeholder image records without leaving the control
              room.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => void query.refetch()}
              disabled={query.isFetching}
              className="border-[#546a7b]/65 bg-[#fdfdff]/70 text-[#393d3f]"
            >
              <RefreshCcw
                className={`mr-2 h-4 w-4 ${query.isFetching ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
            <Button
              type="button"
              onClick={() => void runCleanup()}
              disabled={cleanupPending}
              className="bg-[#62929e] text-[#fdfdff] hover:bg-[#4f7d87]"
            >
              {cleanupPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              Cleanup Images
            </Button>
          </div>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        {summary.map((item) => (
          <article
            key={item.label}
            className="rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-5"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#546a7b]">
              {item.label}
            </p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {item.value}
            </p>
            <p className="mt-1 text-sm text-[#546a7b]">{item.hint}</p>
          </article>
        ))}
      </section>

      <section className="rounded-3xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#546a7b]" />
            <Input
              value={search}
              onChange={(event) =>
                updateParams({ search: event.target.value || undefined })
              }
              placeholder="Search make, model, or stock number"
              className="pl-9"
            />
          </div>
          <div className="w-full lg:w-52">
            <Select
              value={status}
              onValueChange={(value) => updateParams({ status: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="live">Live</SelectItem>
                <SelectItem value="upcoming">Upcoming</SelectItem>
                <SelectItem value="sold">Sold</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Badge
            variant="secondary"
            className="justify-center rounded-xl px-3 py-2"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            Admin access
          </Badge>
        </div>
      </section>

      {query.isError ? (
        <div className="rounded-3xl border border-red-500/35 bg-red-500/10 p-6">
          <p className="text-lg font-semibold text-[#393d3f]">
            Vehicle catalog failed to load
          </p>
          <p className="mt-2 text-sm text-red-700">
            {isAxiosError(query.error)
              ? ((query.error.response?.data as { detail?: string } | undefined)
                  ?.detail ?? query.error.message)
              : "Unknown error"}
          </p>
        </div>
      ) : query.isLoading && vehicles.length === 0 ? (
        <VehicleGridSkeleton />
      ) : vehicles.length > 0 ? (
        <>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            {vehicles.map((vehicle) => (
              <VehicleCard
                key={vehicle.id}
                vehicle={vehicle}
                href={`/admin/vehicles/${vehicle.id}`}
                onDelete={(selectedVehicle) =>
                  void handleDeleteVehicle(
                    selectedVehicle.id,
                    `${selectedVehicle.year} ${selectedVehicle.make} ${selectedVehicle.model}`,
                  )
                }
                deleteDisabled={deletePendingId === vehicle.id}
              />
            ))}
          </div>

          <div className="flex flex-col gap-3 rounded-3xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-[#546a7b]">
              Showing {(page - 1) * PAGE_SIZE + 1} to{" "}
              {Math.min(page * PAGE_SIZE, totalItems)} of {totalItems} vehicles
            </p>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={page <= 1}
                onClick={() => updateParams({ page: String(page - 1) })}
              >
                Previous
              </Button>
              <span className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-4 py-2 text-sm text-[#393d3f]">
                Page {page} of {totalPages}
              </span>
              <Button
                type="button"
                variant="outline"
                disabled={page >= totalPages}
                onClick={() => updateParams({ page: String(page + 1) })}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      ) : (
        <div className="rounded-3xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-10 text-center">
          <p className="text-xl font-semibold text-[#393d3f]">
            No vehicles matched this filter
          </p>
          <p className="mt-2 text-sm text-[#546a7b]">
            Try clearing the search or switching the listing status filter.
          </p>
          <div className="mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push("/admin/vehicles")}
            >
              Clear filters
            </Button>
          </div>
        </div>
      )}

      <div className="text-sm text-[#546a7b]">
        Need a full vehicle edit? Open any listing and use the admin edit panel.{" "}
        <Link
          href="/admin/dashboard"
          className="font-semibold text-[#62929e] hover:underline"
        >
          Return to dashboard
        </Link>
      </div>
    </div>
  );
}
