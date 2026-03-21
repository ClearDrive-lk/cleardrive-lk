"use client";

import { Suspense } from "react";

import VehicleCatalog from "./VehicleCatalog";

export default function VehiclesPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center text-[#393d3f] dark:bg-slate-950 dark:text-slate-100">
          Loading Catalog...
        </div>
      }
    >
      <VehicleCatalog />
    </Suspense>
  );
}
