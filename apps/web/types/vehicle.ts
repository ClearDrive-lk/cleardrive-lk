export interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  price: number;
  mileage: number;
  fuel: string;
  transmission: string;
  status: 'Live' | 'Upcoming' | 'Sold';
  condition: 'New' | 'Used';
  imageUrl?: string;

  // New fields for detailed view & cards
  lotNumber: string;
  grade: string;
  estimatedLandedCostLKR: number;
  priceJPY: number;
  trim: string;
  chassisCode: string;
  engineCC: number;
  endTime: string | Date;
  firstRegistrationDate?: string | Date;
  color?: string;
}

export interface VehicleResponse {
  data: Vehicle[];
  total: number;
  page: number;
  limit: number;
}