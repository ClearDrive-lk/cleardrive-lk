"use client";



import { Suspense, useEffect, useState } from "react";

import { useSearchParams } from "next/navigation";

import axios from "axios";



import AuthGuard from "@/components/auth/AuthGuard";

import {

  OrderWizard,

  OrderWizardVehicle,

} from "@/components/orders/OrderWizard";

import { apiClient } from "@/lib/api-client";

import { Vehicle } from "@/types/vehicle";



const fallbackVehicleImage =

  "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80";



const toOrderWizardVehicle = (vehicle: Vehicle): OrderWizardVehicle => ({

  id: vehicle.id,

  make: vehicle.make,

  model: vehicle.model,

  year: vehicle.year,

  lotNumber: vehicle.lotNumber,

  cifPriceLkr: vehicle.estimatedLandedCostLKR || vehicle.price || 0,

  imageUrl: vehicle.imageUrl || fallbackVehicleImage,

  thumbnails: vehicle.imageUrl ? [vehicle.imageUrl] : [fallbackVehicleImage],

});



function CreateOrderContent() {

  const searchParams = useSearchParams();

  const vehicleId = searchParams.get("vehicleId");



  const [vehicle, setVehicle] = useState<OrderWizardVehicle | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const [loadError, setLoadError] = useState<string | null>(null);



  useEffect(() => {

    if (!vehicleId) {

      setVehicle(null);

      setIsLoading(false);

      setLoadError("Vehicle ID is required to create an order.");

      return;

    }



    let isMounted = true;

    const fetchVehicle = async () => {

      try {

        setIsLoading(true);

        setLoadError(null);

        const response = await apiClient.get(`/vehicles/${vehicleId}`);

        const vehiclePayload = response.data?.data ?? response.data;



        if (!isMounted) return;

        setVehicle(toOrderWizardVehicle(vehiclePayload as Vehicle));

      } catch (error) {

        if (!isMounted) return;

        setVehicle(null);



        if (axios.isAxiosError(error)) {

          const apiMessage =

            (error.response?.data as { detail?: string; message?: string } | undefined)

              ?.detail ??

            (error.response?.data as { detail?: string; message?: string } | undefined)

              ?.message;

          setLoadError(apiMessage || error.message || "Failed to load vehicle.");

          return;

        }



        setLoadError(

          error instanceof Error ? error.message : "Failed to load vehicle.",

        );

      } finally {

        if (isMounted) {

          setIsLoading(false);

        }

      }

    };



    void fetchVehicle();



    return () => {

      isMounted = false;

    };

  }, [vehicleId]);



  return (

    <div className="min-h-screen bg-[#050505] px-6 py-10 text-white">

      <div className="mx-auto max-w-4xl space-y-6">

        <header className="space-y-2">

          <h1 className="text-3xl font-bold tracking-tight">

            Transparent Checkout Wizard

          </h1>

          <p className="text-zinc-400">

            Confirm vehicle details, submit secure shipping information, and

            review your landed cost before placing the order.

          </p>

        </header>



        {isLoading ? (

          <div className="rounded-lg border border-white/10 bg-black/30 p-6 text-zinc-300">

            Loading vehicle details...

          </div>

        ) : null}



        {loadError ? (

          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-red-300">

            {loadError}

          </div>

        ) : null}



        {vehicle && !isLoading && !loadError ? <OrderWizard vehicle={vehicle} /> : null}

      </div>

    </div>

  );

}



export default function CreateOrderPage() {

  return (

    <AuthGuard>

      <Suspense

        fallback={

          <div className="min-h-screen bg-[#050505] px-6 py-10 text-white">

            Loading order creation...

          </div>

        }

      >

        <CreateOrderContent />

      </Suspense>

    </AuthGuard>

  );

}