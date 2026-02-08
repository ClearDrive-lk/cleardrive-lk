"use client";

import { useState, Suspense, useEffect } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import Link from "next/link";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { Terminal, ChevronLeft, Car, Calendar, Gauge, Fuel, Timer, Share2, Mail, Phone, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";
import { useLogout } from "@/lib/hooks/useLogout";
import { useVehicles } from "@/lib/hooks/useVehicles"; // We might need a single vehicle fetch hook or filter by ID
import { apiClient } from "@/lib/api-client";
import { Vehicle } from "@/types/vehicle";
import { useQuery } from "@tanstack/react-query";

// Fetch single vehicle helper
const useVehicle = (id: string) => {
    return useQuery<Vehicle>({
        queryKey: ['vehicle', id],
        queryFn: async () => {
            const response = await apiClient.get(`/vehicles/${id}`);
            return response.data;
        },
        enabled: !!id,
    });
};

function VehicleDetail() {
    const { id } = useParams<{ id: string }>();
    const router = useRouter();
    const { logout, isLoading: isLogoutLoading } = useLogout();
    const { data: vehicle, isLoading, isError } = useVehicle(id);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);

    useEffect(() => {
        if (vehicle?.imageUrl) {
            setSelectedImage(vehicle.imageUrl);
        }
    }, [vehicle]);

    // Formatters
    const formatJPY = new Intl.NumberFormat('ja-JP', { style: 'currency', currency: 'JPY', maximumSignificantDigits: 3 }).format;
    const formatLKR = new Intl.NumberFormat('en-LK', { style: 'currency', currency: 'LKR', maximumSignificantDigits: 3 }).format;
    const formatKm = new Intl.NumberFormat('en-US').format;

    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#050505] flex items-center justify-center text-white">
                <div className="animate-pulse flex flex-col items-center">
                    <Car className="w-12 h-12 text-[#FE7743] mb-4 opacity-50" />
                    <p className="font-mono text-sm text-gray-500">Loading Vehicle Details...</p>
                </div>
            </div>
        );
    }

    if (isError || !vehicle) {
        return (
            <div className="min-h-screen bg-[#050505] flex items-center justify-center text-white">
                <div className="text-center">
                    <h2 className="text-2xl font-bold mb-2">Vehicle Not Found</h2>
                    <Button onClick={() => router.back()} variant="outline" className="border-white/10">Go Back</Button>
                </div>
            </div>
        );
    }

    // Determine images (Mocking multiple images if api only returns one)
    const images = vehicle.imageUrl ? [vehicle.imageUrl, vehicle.imageUrl, vehicle.imageUrl] : [];
    // In a real scenario, vehicle.images would be an array. 
    // Using the single image 3 times for demo of gallery functionality if array not available.

    const estDuty = vehicle.estimatedLandedCostLKR * 0.30;

    const contactAgent = () => {
        const subject = encodeURIComponent(`Inquiry about ${vehicle.year} ${vehicle.make} ${vehicle.model} (${vehicle.lotNumber})`);
        window.location.href = `mailto:sales@cleardrive.lk?subject=${subject}`;
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans flex flex-col">
            {/* Grid Background */}
            <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none z-0" />

            {/* Navigation */}
            <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="font-bold text-xl tracking-tighter flex items-center gap-2">
                        <Terminal className="w-5 h-5 text-[#FE7743]" />
                        ClearDrive<span className="text-[#FE7743]">.lk</span>
                    </Link>
                    <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
                        <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
                        <Link href="/dashboard/vehicles" className="text-white flex items-center gap-2">
                            Vehicles <Badge variant="outline" className="text-[10px] border-[#FE7743]/20 text-[#FE7743]">LIVE</Badge>
                        </Link>
                    </div>
                </div>
            </nav>

            <main className="flex-1 relative z-10 max-w-7xl mx-auto w-full px-6 py-8">
                {/* Breadcrumb / Back */}
                <Button onClick={() => router.back()} variant="ghost" className="mb-6 pl-0 hover:bg-transparent hover:text-[#FE7743] text-gray-400">
                    <ChevronLeft className="w-4 h-4 mr-2" /> Back to Catalog
                </Button>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">

                    {/* LEFT COLUMN: Gallery */}
                    <div className="space-y-4">
                        <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-gray-900 border border-white/10">
                            {selectedImage ? (
                                <Image
                                    src={selectedImage}
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
                                <Badge className="bg-[#FE7743] text-black font-bold border-0">Grade {vehicle.grade}</Badge>
                                {vehicle.condition === 'New' && <Badge className="bg-green-500 text-black font-bold border-0">NEW</Badge>}
                            </div>
                        </div>

                        {/* Thumbnails */}
                        {images.length > 0 && (
                            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-none">
                                {images.map((img, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setSelectedImage(img)}
                                        className={`relative w-24 h-16 rounded overflow-hidden border-2 transition-all flex-shrink-0 ${selectedImage === img ? 'border-[#FE7743]' : 'border-transparent opacity-70 hover:opacity-100'}`}
                                    >
                                        <Image src={img} alt="Thumbnail" fill className="object-cover" />
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* RIGHT COLUMN: Details */}
                    <div className="space-y-8">
                        <div>
                            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                                {vehicle.year} {vehicle.make} <span className="text-[#FE7743]">{vehicle.model}</span>
                            </h1>
                            <p className="text-xl text-gray-400">{vehicle.trim} ({vehicle.chassisCode})</p>

                            <div className="flex items-center gap-4 mt-4 text-sm font-mono text-gray-500">
                                <span className="flex items-center gap-1"><Timer className="w-4 h-4" /> Lot #{vehicle.lotNumber}</span>
                                <span className="w-1 h-1 bg-gray-700 rounded-full" />
                                <span className="flex items-center gap-1"><MapPin className="w-4 h-4" /> USS Tokyo</span>
                            </div>
                        </div>

                        <Separator className="bg-white/10" />

                        {/* Price Card */}
                        <Card className="bg-white/5 border-white/10 overflow-hidden">
                            <CardContent className="p-6">
                                <div className="flex justify-between items-end mb-2">
                                    <span className="text-gray-400 text-sm">Estimated Landed Cost</span>
                                    <span className="text-3xl font-bold text-white">{formatLKR(vehicle.estimatedLandedCostLKR)}</span>
                                </div>
                                <div className="flex justify-between items-center text-sm text-gray-500 font-mono mb-6">
                                    <span>Current Bid: {formatJPY(vehicle.priceJPY)}</span>
                                    <span>Est. Duty: {formatLKR(estDuty)}</span>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <Button onClick={contactAgent} className="bg-[#FE7743] hover:bg-[#FE7743]/90 text-black font-bold h-12">
                                        <Mail className="w-4 h-4 mr-2" /> Contact Agent
                                    </Button>
                                    <Button variant="outline" className="border-white/10 text-white hover:bg-white/5 h-12">
                                        <Share2 className="w-4 h-4 mr-2" /> Share
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Specs Table */}
                        <div>
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Gauge className="w-5 h-5 text-[#FE7743]" /> Specifications
                            </h3>
                            <div className="rounded-lg border border-white/10 overflow-hidden">
                                <Table>
                                    <TableBody>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Make</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.make}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Model</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.model}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Year</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.year}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">First Registration</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.firstRegistrationDate ? new Date(vehicle.firstRegistrationDate).toLocaleDateString() : 'N/A'}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Mileage</TableCell>
                                            <TableCell className="text-white text-right">{formatKm(vehicle.mileage)} km</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Engine</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.engineCC} cc</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Fuel</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.fuel}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Transmission</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.transmission}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-white/5 hover:bg-white/5">
                                            <TableCell className="font-medium text-gray-400">Color</TableCell>
                                            <TableCell className="text-white text-right">{vehicle.color || 'N/A'}</TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
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
        <Suspense fallback={<div className="min-h-screen bg-[#050505] flex items-center justify-center text-white">Loading...</div>}>
            <AuthGuard>
                <VehicleDetail />
            </AuthGuard>
        </Suspense>
    );
}
