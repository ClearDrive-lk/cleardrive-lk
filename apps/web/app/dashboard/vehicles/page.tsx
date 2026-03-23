import { Suspense } from "react";
import VehicleCatalog from "./VehicleCatalog";

export const dynamic = "force-dynamic";

type VehiclesPageProps = {
  searchParams?:
    | Record<string, string | string[] | undefined>
    | Promise<Record<string, string | string[] | undefined>>;
};

export default async function VehiclesPage({
  searchParams,
}: VehiclesPageProps) {
  const resolvedSearchParams = await searchParams;
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center text-[#393d3f]">
          Loading Catalog...
        </div>
      }
    >
      <VehicleCatalog searchParams={resolvedSearchParams} />
    </Suspense>
  );
}
